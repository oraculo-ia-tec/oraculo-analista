# ============================================================
# src/hooks/audit_hook.py
# Hook de auditoria — registra cada chamada ao LLM
# ============================================================
from __future__ import annotations

from ..utils.helpers import now_iso


class AuditHook:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, entry: dict) -> None:
        entry.setdefault("ts", now_iso())
        self._log.append(entry)

    def get_log(self) -> list[dict]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
