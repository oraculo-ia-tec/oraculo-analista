# ============================================================
# src/utils/helpers.py
# Utilitários reutilizáveis em todo o projeto
# ============================================================
import re
import time
import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """Gera um ID único com prefixo opcional."""
    uid = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{prefix}{uid}" if prefix else uid


def now_iso() -> str:
    """Retorna timestamp ISO 8601 atual."""
    return datetime.utcnow().isoformat() + "Z"


def truncate(text: str, limit: int = 12000) -> str:
    """Trunca texto ao limite de caracteres com aviso."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[Conteúdo truncado por limite de contexto.]"


def strip_think_tags(text: str) -> str:
    """Remove blocos <think>...</think> do output do LLM."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def estimate_tokens(text: str) -> int:
    """Estimativa rápida: ~4 chars por token."""
    return max(1, len(text) // 4)


def retry(func, retries: int = 3, delay: float = 1.5):
    """Executa `func` com retentativas em caso de exceção."""
    last_exc = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay * (attempt + 1))
    raise last_exc
