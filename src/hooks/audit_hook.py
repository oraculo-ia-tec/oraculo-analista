# ============================================================
# src/hooks/audit_hook.py
# Hook de auditoria — registra todas as chamadas ao LLM
# ============================================================
from __future__ import annotations
from datetime import datetime, timezone


class AuditHook:
    def __init__(self):
        self._log: list[dict] = []

    def on_llm_call(self, model: str, prompt_len: int) -> None:
        self._log.append({
            "event":      "llm_call",
            "model":      model,
            "prompt_len": prompt_len,
            "ts":         datetime.now(timezone.utc).isoformat(),
        })

    def on_error(self, source: str, message: str) -> None:
        self._log.append({
            "event":   "error",
            "source":  source,
            "message": message,
            "ts":      datetime.now(timezone.utc).isoformat(),
        })

    def get_log(self) -> list[dict]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
