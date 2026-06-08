"""
Runtime — Oráculo Analista v2.0

Gerencia o ciclo de vida completo de uma sessão:
  1. Inicializa todos os hooks (permissão, custo, auditoria)
  2. Registra os hooks na HookChain global
  3. Expõe método único process() para o app.py
  4. Finaliza a sessão (salva memória, logs)

Uma instância de Runtime por sessão do usuário.
"""
import os
from typing import Generator, Optional

from src.cost_tracker import CostTracker
from src.hooks.audit_hook import AuditHook
from src.hooks.base import hook_chain
from src.hooks.cost_hook import CostHook
from src.hooks.permission_hook import PermissionHook
from src.memory.memory_manager import MemoryManager
from src.memory.session_store import SessionStore
from src.query_engine import QueryEngine
from src.query_engine_factory import create_engine
from src.utils.helpers import generate_id


class Runtime:
    """
    Orquestrador de sessão.
    Instanciado uma vez por login no app.py e armazenado no st.session_state.
    """

    def __init__(
        self,
        user_id: str,
        user_name: str = "",
        user_email: str = "",
        user_plan: str = "free",
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.user_plan = user_plan

        # Componentes principais
        self.engine: QueryEngine = create_engine(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_plan=user_plan,
        )
        self.cost_tracker = CostTracker()
        self.session_store = SessionStore(user_id=user_id)

        # Registra hooks na cadeia global
        self._register_hooks()

    # ─── Hooks ────────────────────────────────────────────────────────────────

    def _register_hooks(self) -> None:
        """Registra os 3 hooks padrão na HookChain global."""
        session = self.engine.session

        hook_chain.register(PermissionHook(user_plan=self.user_plan))
        hook_chain.register(CostHook(session=session))
        hook_chain.register(AuditHook(
            session_id=session.session_id,
            user_id=self.user_id,
        ))

    # ─── Processamento de mensagens ───────────────────────────────────────────

    def process(self, user_input: str) -> str:
        """Processa uma mensagem do usuário. Retorna a resposta final."""
        return self.engine.run(user_input)

    def process_stream(self, user_input: str) -> Generator[str, None, None]:
        """Versão streaming — yield de chunks para o Streamlit."""
        yield from self.engine.run_stream(user_input)

    # ─── Documentos ───────────────────────────────────────────────────────────

    def load_document(self, filepath: str, filename: str) -> str:
        """Carrega um documento na sessão ativa."""
        return self.engine.load_document(filepath=filepath, filename=filename)

    @property
    def active_document(self) -> Optional[str]:
        return self.engine.session.active_document

    # ─── Métricas ─────────────────────────────────────────────────────────────

    def get_metrics(self) -> dict:
        """Retorna métricas da sessão para exibição na sidebar."""
        session = self.engine.session
        return {
            "messages": len(session.messages),
            "tool_calls": session.tool_calls_count,
            "tokens": session.total_tokens,
            "cost_usd": self.cost_tracker.total_cost_usd,
            "cost_brl": self.cost_tracker.total_cost_brl,
            "document": session.active_document or "Nenhum",
        }

    # ─── Finalização da sessão ────────────────────────────────────────────────

    def close(self) -> None:
        """
        Finaliza a sessão:
          - Salva histórico no SessionStore
          - Registra sessão na memória do usuário
          - Flush do log de auditoria
        """
        session = self.engine.session
        memory = self.engine.memory

        # Salva sessão
        self.session_store.save(session)

        # Registra na memória do usuário
        memory.record_session(
            session_id=session.session_id,
            messages_count=len(session.messages),
            tokens_used=session.total_tokens,
            tools_used=session.tool_calls_count,
            document=session.active_document,
        )
