# ============================================================
# src/runtime.py
# Runtime principal — gerencia o loop de sessão agêntica
# Equivalente ao runtime.py do Claude Code
# ============================================================
from __future__ import annotations

import streamlit as st

from .constants.settings import (
    APP_NAME,
    DEFAULT_MODEL,
    MAX_TOKENS_FREE_PLAN,
    MAX_TOKENS_PRO_PLAN,
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
from .utils.secrets import get_secret


class Runtime:
    """
    Orquestra o loop completo de uma sessão:

      1. Inicializa hooks, tools, permissões e QueryEngine
      2. Recebe o input do usuário
      3. Monta o system prompt com contexto de arquivos + tools
      4. Chama o QueryEngine (que chama o LLM)
      5. Persiste a mensagem no histórico
      6. Retorna o texto gerado

    Design: um Runtime por sessão Streamlit.
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

        self.permissions = Permissions(permission_overrides)

        self.tools = ToolRegistry()
        self._register_default_tools()

        # Leitura da chave com fallback: st.secrets[groq] → st.secrets → os.environ
        key = api_key or get_secret("GROQ_API_KEY", section="groq")
        self.engine = QueryEngine(
            api_key=key,
            model=model,
            max_tokens=max_tokens,
            cost_hook=self.cost_hook,
            audit_hook=self.audit_hook,
        )

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

        self._save_turn(user_input, response)
        return response

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

    def _register_default_tools(self) -> None:
        file_tool   = FileReadTool()
        search_tool = WebSearchTool()
        export_tool = ExportTool()

        self.tools.register(
            name=file_tool.name,
            description=file_tool.description,
            func=file_tool,
            permission=file_tool.permission,
        )
        self.tools.register(
            name=search_tool.name,
            description=search_tool.description,
            func=search_tool,
            permission=search_tool.permission,
        )
        self.tools.register(
            name=export_tool.name,
            description=export_tool.description,
            func=export_tool,
            permission=export_tool.permission,
        )

    def _build_system_prompt(self, file_context: str) -> str:
        nome   = st.session_state.get("primeiro_nome", "Usuário")
        tools  = self.tools.describe_for_prompt()
        ctx    = truncate(file_context, MAX_CONTEXT_CHARS)

        return f"""Você é o {APP_NAME}, doutor e especialista em análise de dados, \
desenvolvido pela equipe Oráculo IA Tec.
Responda com objetividade, precisão e clareza em português brasileiro.
Se a informação não estiver disponível no contexto, diga isso claramente.
Usuário atual: {nome}

{tools}

## Contexto dos arquivos carregados:
{ctx if ctx else 'Nenhum arquivo carregado nesta sessão.'}
"""

    def _get_history(self) -> list[dict]:
        return [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.get("messages", [])
            if m["role"] in ("user", "assistant")
        ]

    def _save_turn(self, user_input: str, response: str) -> None:
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        st.session_state["messages"].append(
            {"role": "user",      "content": user_input}
        )
        st.session_state["messages"].append(
            {"role": "assistant", "content": response}
        )
