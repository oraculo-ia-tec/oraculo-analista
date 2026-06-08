"""
Audit Hook — registra todas as execuções de tools em log de auditoria.
Gera trilha completa de ações do agente por sessão.
"""
import json
import os
from datetime import datetime
from typing import Optional
from src.hooks.base import BaseHook
from src.types.base import ToolCall, ToolResult


AUDIT_LOG_DIR = "logs/audit"
os.makedirs(AUDIT_LOG_DIR, exist_ok=True)


class AuditHook(BaseHook):
    """
    Grava um log JSON por sessão com cada tool call:
      - timestamp
      - tool_name
      - parâmetros (sanitizados)
      - sucesso/erro
      - duração em ms
    """

    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self._start_times: dict = {}
        self._log_file = os.path.join(
            AUDIT_LOG_DIR, f"{session_id}.jsonl"
        )

    def before_tool(self, tool_call: ToolCall) -> Optional[ToolResult]:
        """Registra timestamp de início."""
        self._start_times[tool_call.tool_id] = datetime.utcnow().timestamp()
        return None  # Não bloqueia

    def after_tool(self, tool_call: ToolCall, result: ToolResult) -> ToolResult:
        """Grava entrada no log JSONL."""
        start = self._start_times.pop(tool_call.tool_id, None)
        duration_ms = None
        if start:
            duration_ms = round((datetime.utcnow().timestamp() - start) * 1000)

        # Sanitiza parâmetros (remove conteúdo de arquivos, mantém metadados)
        safe_params = self._sanitize_params(tool_call.parameters)

        entry = {
            "ts": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tool": tool_call.tool_name,
            "params": safe_params,
            "success": result.success,
            "error": result.error,
            "duration_ms": duration_ms,
        }

        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # Log não-crítico — não interrompe o fluxo

        return result

    def _sanitize_params(self, params: dict) -> dict:
        """Remove campos com conteúdo longo (filepath mantido, content removido)."""
        safe = {}
        for k, v in params.items():
            if isinstance(v, str) and len(v) > 200:
                safe[k] = f"[{len(v)} chars]"
            else:
                safe[k] = v
        return safe
