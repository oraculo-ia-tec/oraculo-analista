"""Recuperação de senha — modelo de tabela e utilitários.

Tabela `password_reset` armazena tokens emitidos para redefinição
de senha. Cada token é único, possui validade (padrão: 60 minutos)
e marca de uso (one-shot).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, Integer, String

TOKEN_TTL_MINUTOS = 60


def register_model(Base):
    """Registra o modelo PasswordReset usando o Base do app principal."""

    class PasswordReset(Base):
        __tablename__ = 'password_reset'

        id = Column(Integer, primary_key=True, autoincrement=True)
        email = Column(String(255), nullable=False, index=True)
        token = Column(String(128), unique=True, nullable=False, index=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        expires_at = Column(DateTime, nullable=False)
        used = Column(Boolean, default=False, nullable=False)

    return PasswordReset


def gerar_token() -> str:
    return secrets.token_urlsafe(48)


def criar_token_para(session, PasswordReset, email: str) -> str:
    """Invalida tokens anteriores do e-mail e cria um novo."""
    email = (email or '').strip().lower()
    # Invalida tokens anteriores não utilizados
    session.query(PasswordReset).filter(
        PasswordReset.email == email,
        PasswordReset.used.is_(False),
    ).update({PasswordReset.used: True})

    token = gerar_token()
    novo = PasswordReset(
        email=email,
        token=token,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTOS),
        used=False,
    )
    session.add(novo)
    session.commit()
    return token


def validar_token(session, PasswordReset, token: str):
    """Retorna o registro PasswordReset válido ou None."""
    if not token:
        return None
    reg = session.query(PasswordReset).filter_by(token=token).first()
    if not reg:
        return None
    if reg.used:
        return None
    if reg.expires_at < datetime.utcnow():
        return None
    return reg


def consumir_token(session, PasswordReset, token: str) -> bool:
    reg = session.query(PasswordReset).filter_by(token=token).first()
    if not reg:
        return False
    reg.used = True
    session.commit()
    return True


def atualizar_senha(session, UserAnalise, email: str, nova_senha: str) -> bool:
    """Atualiza o hash de senha do usuário pelo e-mail."""
    email = (email or '').strip().lower()
    user = session.query(UserAnalise).filter_by(email=email).first()
    if not user:
        return False
    user.password = bcrypt.hashpw(
        nova_senha.encode(), bcrypt.gensalt()
    ).decode()
    session.commit()
    return True
