# ============================================================
# src/utils/helpers.py
# Funções utilitárias compartilhadas
# ============================================================
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone


def truncate(text: str, limite: int = 10_000) -> str:
    """Trunca texto ao limite de caracteres, adicionando aviso se necessário."""
    if len(text) <= limite:
        return text
    return text[:limite] + f"\n\n[... texto truncado após {limite} caracteres ...]"


def strip_think_tags(text: str) -> str:
    """Remove blocos <think>...</think> da resposta do modelo."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def estimate_tokens(text: str) -> int:
    """Estimativa grosseira: ~4 caracteres por token."""
    return max(1, len(text) // 4)


def generate_id(prefix: str = "") -> str:
    """Gera um ID único com prefixo opcional."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    """Retorna timestamp atual em ISO 8601 UTC."""
    return datetime.now(timezone.utc).isoformat()
