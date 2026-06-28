# ============================================================
# src/runtime.py
# Runtime principal — gerencia o loop de sessão agêntica
# Versão 3.0: system prompt avançado + memória de sessão
# ============================================================
from __future__ import annotations

import streamlit as st

from .constants.settings import (
    APP_NAME,
    DEFAULT_MODEL,
    MAX_TOKENS_FREE_PLAN,
    MAX_CONTEXT_CHARS,
)
from .query_engine import QueryEngine
from .permissions import Permissions
from .hooks.cost_hook import CostHook
from .hooks.audit_hook import AuditHook
from .tools.registry import ToolRegistry
from .tools.file_tools import FileReadTool
from .tools.search_tool import WebSearchTool
from .tools.export_tool import ExportTool
from .utils.helpers import truncate, generate_id, now_iso
from .prompt.system_prompt import build as build_system_prompt
from .memory.session_memory import SessionMemory


class Runtime:
    """
    Orquestra o loop completo de uma sessão agêntica.

    v3.0 — melhorias:
      - system prompt rico via src/prompt/system_prompt.py
      - memória de sessão via src/memory/session_memory.py
      - audit_log exposto no st.session_state para o Dashboard Admin
      - cost_hook exposto no st.session_state para o Dashboard Admin
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS_FREE_PLAN,
        permission_overrides: dict | None = None,
    ):
        self.session_id  = generate_id("sess_")
        self.started_at  = now_iso()

        self.cost_hook  = CostHook()
        self.audit_hook = AuditHook()

        # Expõe hooks no session_state para o Dashboard Admin ler
        st.session_state["_cost_hook"]  = self.cost_hook
        st.session_state["_audit_log"]  = self.audit_hook.get_log()

        self.permissions = Permissions(permission_overrides)

        self.tools = ToolRegistry()
        self._register_default_tools()

        if api_key:
            key = api_key
        else:
            try:
                key = st.secrets["groq"]["GROQ_API_KEY"]
            except Exception:
                key = ""

        self.engine = QueryEngine(
            api_key=key,
            model=model,
            max_tokens=max_tokens,
            cost_hook=self.cost_hook,
            audit_hook=self.audit_hook,
        )

    # ── público ───────────────────────────────────────
    def run(
        self,
        user_input: str,
        file_context: str = "",
        stream_callback=None,
    ) -> str:
        system_prompt = self._build_system_prompt(file_context)
        history       = self._get_history()

        response = self.engine.query(
            system_prompt=system_prompt,
            user_prompt=user_input,
            history=history,
            stream_callback=stream_callback,
        )

        # Registra turno na memória e no audit
        SessionMemory.registrar_turno(user_input, response)
        self.audit_hook.log({
            "prompt":       user_input[:120],
            "total_tokens": self.cost_hook.summary()["total_tokens"],
        })
        st.session_state["_audit_log"] = self.audit_hook.get_log()

        self._save_turn(user_input, response)
        return response

    def registrar_arquivo(self, nome: str) -> None:
        """Chame após carregar um arquivo para registrar na memória."""
        SessionMemory.registrar_arquivo(nome)

    def get_cost_summary(self) -> dict:
        return self.cost_hook.summary()

    def get_audit_log(self) -> list[dict]:
        return self.audit_hook.get_log()

    def reset_session(self) -> None:
        st.session_state["messages"]             = []
        st.session_state["arquivos_processados"] = []
        st.session_state["full_content"]         = ""
        self.cost_hook.reset()
        self.audit_hook.clear()
        SessionMemory.reset()
        st.session_state["_audit_log"] = []

    # ── privado ───────────────────────────────────────
    def _register_default_tools(self) -> None:
        for tool in [FileReadTool(), WebSearchTool(), ExportTool()]:
            self.tools.register(
                name=tool.name,
                description=tool.description,
                func=tool,
                permission=tool.permission,
            )

    def _build_system_prompt(self, file_context: str) -> str:
        nome          = st.session_state.get("primeiro_nome", "Usuário")
        memoria_str   = SessionMemory.to_prompt_str()
        tools_desc    = self.tools.describe_for_prompt()

        return build_system_prompt(
            nome_usuario=nome,
            file_context=file_context,
            memoria_sessao=memoria_str,
            tools_desc=tools_desc,
        )

    def _get_history(self) -> list[dict]:
        msgs = st.session_state.get("messages", [])
        return [
            {"role": m["role"], "content": m["content"]}
            for m in msgs
            if m["role"] in ("user", "assistant")
        ]

    def _save_turn(self, user_input: str, response: str) -> None:
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        st.session_state["messages"].append({"role": "user",      "content": user_input})
        st.session_state["messages"].append({"role": "assistant", "content": response})
