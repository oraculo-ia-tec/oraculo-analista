# ============================================================
# src/memory/memory_manager.py
# Gerenciador de memória por usuário (stub expansível)
# ============================================================
from __future__ import annotations


class MemoryManager:
    """
    Gerencia memória persistente por usuário.
    Versão atual: memória em RAM por sessão.
    Expansível para banco de dados (Supabase, Redis, etc.)
    """

    def __init__(self, user_id: str, user_name: str = "", user_email: str = ""):
        self.user_id    = user_id
        self.user_name  = user_name
        self.user_email = user_email
        self._store: dict[str, str] = {}

    def get(self, key: str, default: str = "") -> str:
        return self._store.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()

    def as_context(self) -> str:
        if not self._store:
            return ""
        lines = [f"- {k}: {v}" for k, v in self._store.items()]
        return "## Memória do usuário:\n" + "\n".join(lines)
