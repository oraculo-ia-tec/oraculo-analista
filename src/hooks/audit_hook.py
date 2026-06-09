# ============================================================
# src/hooks/audit_hook.py
# Hook de auditoria — registra eventos de tools e chamadas LLM
# ============================================================
from ..utils.helpers import now_iso, generate_id


class AuditHook:
    """
    Mantém um log de auditoria em memória para a sessão.
    Cada evento registra: id, tipo, timestamp, detalhes.
    """

    def __init__(self):
        self._log: list[dict] = []

    def record(self, event_type: str, details: dict) -> str:
        entry = {
            "id":        generate_id("evt_"),
            "type":      event_type,
            "timestamp": now_iso(),
            "details":   details,
        }
        self._log.append(entry)
        return entry["id"]

    def on_tool_call(self, tool_name: str, params: dict) -> str:
        return self.record("tool_call", {"tool": tool_name, "params": params})

    def on_tool_result(self, tool_name: str, result: str) -> str:
        return self.record("tool_result", {"tool": tool_name, "result_preview": result[:200]})

    def on_llm_call(self, model: str, prompt_len: int) -> str:
        return self.record("llm_call", {"model": model, "prompt_chars": prompt_len})

    def on_error(self, source: str, error: str) -> str:
        return self.record("error", {"source": source, "error": error})

    def get_log(self) -> list[dict]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
