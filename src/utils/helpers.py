# ============================================================
# src/utils/helpers.py
# Funções utilitárias gerais
# ============================================================
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def truncate(text: str, limite: int = 6000) -> str:
    """Trunca texto ao limite de caracteres."""
    if len(text) <= limite:
        return text
    return text[:limite] + "\n\n[... conteúdo truncado ...]"


def estimate_tokens(text: str) -> int:
    """Estima tokens de forma simples (4 chars ≈ 1 token)."""
    return max(1, len(text) // 4)


def generate_id(prefix: str = "") -> str:
    """Gera um ID único com prefixo opcional."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    """Retorna timestamp ISO 8601 UTC."""
    return datetime.now(timezone.utc).isoformat()
