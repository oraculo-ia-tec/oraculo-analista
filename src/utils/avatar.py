# ============================================================
# src/utils/avatar.py
# Helpers de avatar — leitura e escrita da imagem de perfil
# Imagem é persistida como Base64 no banco (sobrevive a deploys)
# ============================================================
from __future__ import annotations

import base64
import io
import os

DEFAULT_AVATAR = "./src/img/usuario.jpg"


def image_to_b64(file_like) -> str:
    """Converte um file-like object (upload) para string Base64."""
    file_like.seek(0)
    return base64.b64encode(file_like.read()).decode("utf-8")


def b64_to_bytes(b64: str) -> bytes:
    """Converte Base64 de volta para bytes (para st.image)."""
    return base64.b64decode(b64)


def get_avatar(user) -> str | bytes:
    """
    Retorna a imagem de perfil do usuário na melhor fonte disponível:
    1. Base64 salvo no banco  → bytes (prioridade — persiste entre deploys)
    2. Arquivo local          → path string (compat retroativa)
    3. Avatar padrão         → path string
    """
    # 1. Base64 no banco
    b64 = getattr(user, "profile_image_b64", None)
    if b64:
        try:
            return b64_to_bytes(b64)
        except Exception:
            pass

    # 2. Arquivo local (pode não existir em deploy)
    path = getattr(user, "profile_image_path", None)
    if path and os.path.exists(path):
        return path

    # 3. Avatar padrão
    return DEFAULT_AVATAR
