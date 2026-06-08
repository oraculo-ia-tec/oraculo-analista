"""
Gerenciador de estado global da aplicação.
Store centralizado — padrão Redux simplificado.
"""
from typing import Dict, Any, Optional
from src.types.base import SessionState


class GlobalStore:
    """
    Store singleton que mantém o estado global da aplicação.
    Evita passar estado por parâmetros em toda a cadeia de chamadas.
    """
    _instance: Optional["GlobalStore"] = None
    _state: Dict[str, Any] = {}
    _sessions: Dict[str, SessionState] = {}

    def __new__(cls) -> "GlobalStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._state = {
                "app_ready": False,
                "active_sessions": 0,
                "total_requests": 0,
                "total_tokens_used": 0,
            }
            cls._sessions = {}
        return cls._instance

    # ─── Estado global ─────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def increment(self, key: str, amount: int = 1) -> int:
        current = self._state.get(key, 0)
        self._state[key] = current + amount
        return self._state[key]

    # ─── Gerenciamento de sessões ───────────────────────────────────────────────

    def register_session(self, session: SessionState) -> None:
        """Registra uma nova sessão ativa."""
        self._sessions[session.session_id] = session
        self.increment("active_sessions")

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Recupera uma sessão pelo ID."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Fecha e remove uma sessão do store."""
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            del self._sessions[session_id]
            active = self._state.get("active_sessions", 1)
            self._state["active_sessions"] = max(0, active - 1)

    def get_all_sessions(self) -> Dict[str, SessionState]:
        """Retorna todas as sessões ativas."""
        return dict(self._sessions)

    # ─── Telemetria simples ─────────────────────────────────────────────────────

    def record_request(self, tokens_used: int = 0) -> None:
        """Registra uma requisição ao LLM para telemetria."""
        self.increment("total_requests")
        self.increment("total_tokens_used", tokens_used)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais da aplicação."""
        return {
            "active_sessions": self._state.get("active_sessions", 0),
            "total_requests": self._state.get("total_requests", 0),
            "total_tokens_used": self._state.get("total_tokens_used", 0),
            "sessions_in_store": len(self._sessions),
        }
