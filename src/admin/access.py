# ============================================================
# src/admin/access.py
# Controle de acesso ao Dashboard Admin
# ============================================================
from __future__ import annotations

import streamlit as st

from ..models.base import Session
from ..models.user import Cargo

# Cargos com acesso ao painel admin
ADMIN_CARGOS = {"admin", "gestor", "master", "dev", "desenvolvedor"}


def cargo_do_usuario(user) -> str:
    """Retorna o nome do cargo do usuário em lowercase."""
    try:
        with Session() as session:
            cargo = session.query(Cargo).filter_by(id=user.cargo_id).first()
            return cargo.nome.lower() if cargo else ""
    except Exception:
        return ""


def tem_acesso_admin(user) -> bool:
    """Retorna True se o usuário tem cargo com acesso ao Dashboard."""
    if not user:
        return False
    cargo = cargo_do_usuario(user)
    return any(a in cargo for a in ADMIN_CARGOS)
