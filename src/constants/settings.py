# ============================================================
# src/constants/settings.py
# Constantes globais da aplicação — sem dependências externas
# ============================================================

APP_NAME = "Oráculo Analista"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

MAX_TOKENS_FREE_PLAN = 4096
MAX_TOKENS_PRO_PLAN  = 8192
MAX_CONTEXT_CHARS    = 40_000
MAX_HISTORY_MESSAGES = 20

DEFAULT_PERMISSIONS = {
    "file_read":   "allow",
    "file_write":  "ask",
    "web_search":  "allow",
    "export":      "allow",
    "shell":       "deny",
}
