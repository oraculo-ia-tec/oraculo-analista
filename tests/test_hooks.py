"""
Testes automatizados — Sistema de Hooks

Cobre:
  - PermissionHook: permite/bloqueia por plano
  - CostHook: bloqueia quando acima do limite
  - AuditHook: gera log JSONL correto
  - HookChain: execução em cadeia
"""
import os
import json
import tempfile
import pytest

from src.hooks.base import HookChain
from src.hooks.permission_hook import PermissionHook
from src.hooks.cost_hook import CostHook
from src.hooks.audit_hook import AuditHook
from src.types.base import SessionState
from src.utils.helpers import generate_id


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def session_free():
    return SessionState(
        session_id="sess_free",
        user_id="user_free",
        messages=[],
        total_tokens=0,
        tool_calls_count=0,
        active_document=None,
    )


@pytest.fixture
def session_over_limit():
    """Sessão com tokens próximos ao limite do plano free."""
    return SessionState(
        session_id="sess_over",
        user_id="user_over",
        messages=[],
        total_tokens=48000,  # 96% do limite free (50.000)
        tool_calls_count=0,
        active_document=None,
    )


# ─── PermissionHook ───────────────────────────────────────────────────────────

class TestPermissionHook:
    def test_free_permite_tool_basica(self, session_free):
        hook = PermissionHook(user_plan="free")
        result = hook.before_tool("tool_calculator", {}, session_free)
        assert result["allowed"] is True

    def test_free_bloqueia_tool_premium(self, session_free):
        hook = PermissionHook(user_plan="free")
        result = hook.before_tool("tool_excel", {}, session_free)
        assert result["allowed"] is False
        assert "upgrade" in result["reason"].lower()

    def test_pro_permite_tool_excel(self, session_free):
        hook = PermissionHook(user_plan="pro")
        result = hook.before_tool("tool_excel", {}, session_free)
        assert result["allowed"] is True

    def test_enterprise_permite_tudo(self, session_free):
        hook = PermissionHook(user_plan="enterprise")
        for tool in ["tool_calculator", "tool_excel", "tool_pdf", "tool_chart_generator"]:
            result = hook.before_tool(tool, {}, session_free)
            assert result["allowed"] is True


# ─── CostHook ─────────────────────────────────────────────────────────────────

class TestCostHook:
    def test_permite_quando_abaixo_limite(self, session_free):
        hook = CostHook(session=session_free)
        result = hook.before_tool("tool_calculator", {}, session_free)
        assert result["allowed"] is True

    def test_bloqueia_quando_acima_limite(self, session_over_limit):
        hook = CostHook(session=session_over_limit)
        # tool pesada (PDF) deve ser bloqueada acima de 90%
        result = hook.before_tool("tool_pdf", {}, session_over_limit)
        assert result["allowed"] is False

    def test_permite_tool_leve_mesmo_proximo_limite(self, session_over_limit):
        hook = CostHook(session=session_over_limit)
        # calculator é leve, não deve ser bloqueada
        result = hook.before_tool("tool_calculator", {}, session_over_limit)
        assert result["allowed"] is True


# ─── AuditHook ────────────────────────────────────────────────────────────────

class TestAuditHook:
    def test_gera_arquivo_de_log(self, session_free, tmp_path):
        hook = AuditHook(
            session_id="sess_audit",
            user_id="user_audit",
            log_dir=str(tmp_path),
        )
        hook.before_tool("tool_calculator", {"expression": "1+1"}, session_free)
        hook.after_tool("tool_calculator", {"result": 2}, session_free, success=True)

        log_file = tmp_path / "sess_audit.jsonl"
        assert log_file.exists()

    def test_formato_jsonl(self, session_free, tmp_path):
        hook = AuditHook(
            session_id="sess_fmt",
            user_id="user_fmt",
            log_dir=str(tmp_path),
        )
        hook.after_tool("tool_calculator", {"result": 4}, session_free, success=True)

        log_file = tmp_path / "sess_fmt.jsonl"
        with open(log_file) as f:
            line = json.loads(f.readline())

        assert "ts" in line
        assert line["tool"] == "tool_calculator"
        assert line["success"] is True


# ─── HookChain ────────────────────────────────────────────────────────────────

class TestHookChain:
    def test_cadeia_vazia_permite_tudo(self, session_free):
        chain = HookChain()
        result = chain.run_before("tool_calculator", {}, session_free)
        assert result["allowed"] is True

    def test_cadeia_com_um_hook(self, session_free):
        chain = HookChain()
        chain.register(PermissionHook(user_plan="pro"))
        result = chain.run_before("tool_excel", {}, session_free)
        assert result["allowed"] is True

    def test_cadeia_para_no_primeiro_bloqueio(self, session_free):
        chain = HookChain()
        chain.register(PermissionHook(user_plan="free"))  # bloqueia tool_excel
        chain.register(PermissionHook(user_plan="enterprise"))  # permitiria
        result = chain.run_before("tool_excel", {}, session_free)
        assert result["allowed"] is False  # para no primeiro
