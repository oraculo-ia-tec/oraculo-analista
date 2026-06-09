# ============================================================
# src/constants/settings.py
# Constantes globais do Oráculo Analista (estilo Claude Code)
# ============================================================
from decouple import config

# ── Modelos ──────────────────────────────────────────────────
DEFAULT_MODEL        = config("GROQ_MODEL", default="llama-3.3-70b-versatile")
FALLBACK_MODEL       = "llama-3.1-8b-instant"

# ── Limites de tokens por plano ──────────────────────────────
MAX_TOKENS_FREE_PLAN  = 800
MAX_TOKENS_PRO_PLAN   = 2400
MAX_TOKENS_ULTRA_PLAN = 4096

# ── Janela de contexto ────────────────────────────────────────
MAX_HISTORY_MESSAGES  = 10     # mensagens passadas enviadas ao LLM
MAX_CONTEXT_CHARS     = 14000  # chars máximos do contexto de arquivos

# ── Custo estimado (USD por 1M tokens) ───────────────────────
COST_PER_1M_INPUT_TOKENS   = 0.59   # llama-3.3-70b groq pricing
COST_PER_1M_OUTPUT_TOKENS  = 0.79

# ── Permissões padrão ────────────────────────────────────────
DEFAULT_PERMISSIONS = {
    "file_read":    "allow",
    "file_write":   "ask",
    "web_search":   "allow",
    "code_exec":    "deny",
    "send_email":   "ask",
    "billing":      "ask",
}

# ── Versão ───────────────────────────────────────────────────
APP_VERSION = "2.0.0"
APP_NAME    = "Oráculo Analista"
