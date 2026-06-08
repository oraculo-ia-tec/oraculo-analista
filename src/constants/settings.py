"""
Constantes globais da Arquitetura Claude Code — Oráculo Analista
Todas as configurações fixas do sistema ficam aqui.
"""
from pathlib import Path

# ─── Identidade ────────────────────────────────────────────────────────────────
APP_NAME = "Oráculo Analista"
APP_VERSION = "2.0.0"  # versão pós-implementação da arquitetura Claude Code

# ─── Limites de tokens ─────────────────────────────────────────────────────────
MAX_TOKENS_PER_SESSION = 128_000    # janela de contexto máxima por sessão
MAX_TOKENS_PER_MESSAGE = 8_192      # máximo de tokens em uma única resposta
MAX_TOOL_CALLS_PER_SESSION = 50     # evita loops infinitos de tools

# ─── Limites de documentos ─────────────────────────────────────────────────────
MAX_DOCUMENT_SIZE_MB = 25           # tamanho máximo de upload
SUPPORTED_DOCUMENT_TYPES = [
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".md",
]

# ─── Modelos LLM (Groq) ────────────────────────────────────────────────────────
DEFAULT_MODEL = "llama-3.3-70b-versatile"   # modelo principal
FALLBACK_MODEL = "llama-3.1-8b-instant"     # fallback quando quota estiver apertada

# ─── Timeouts ──────────────────────────────────────────────────────────────────
TOOL_TIMEOUT_SECONDS = 30           # timeout máximo para execução de uma tool

# ─── Caminhos ──────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent
MEMORY_DIR = ROOT_DIR / "user_profiles"     # onde ficam os MEMORY.md dos usuários
DB_PATH = ROOT_DIR / "oraculo_analista.db"  # banco SQLite

# ─── Planos e limites por plano ────────────────────────────────────────────────
PLANS = {
    "free": {
        "label": "Gratuito",
        "max_sessions_per_day": 3,
        "max_tokens_per_session": 32_000,
        "max_documents_per_session": 1,
        "tools_allowed": ["tool_pdf", "tool_excel", "tool_txt"],
    },
    "pro": {
        "label": "Pro",
        "max_sessions_per_day": 50,
        "max_tokens_per_session": 128_000,
        "max_documents_per_session": 5,
        "tools_allowed": ["tool_pdf", "tool_excel", "tool_txt", "tool_email", "tool_asaas"],
    },
    "enterprise": {
        "label": "Enterprise",
        "max_sessions_per_day": -1,  # ilimitado
        "max_tokens_per_session": 128_000,
        "max_documents_per_session": -1,
        "tools_allowed": "all",
    },
}
