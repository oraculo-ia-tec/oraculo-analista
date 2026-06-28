# ============================================================
# src/auth/service.py
# Lógica de autenticação
# ============================================================
from __future__ import annotations

import logging
import os
import random
import string

import bcrypt
import streamlit as st
from sqlalchemy.orm import make_transient

from ..models.base import Session
from ..models.user import UserAnalise
from notification import Notificador

PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

logger = logging.getLogger("auth")


def _gerar_codigo(tamanho: int = 6) -> str:
    return "".join(random.choices(string.digits, k=tamanho))


def _save_profile_image(image, user_email: str) -> str | None:
    if image is None:
        return None
    path = os.path.join(PROFILE_IMAGES_DIR, f"{user_email}.png")
    with open(path, "wb") as f:
        f.write(image.getbuffer())
    return path


def _enviar_codigo(email: str, nome: str, codigo: str) -> bool:
    """Tenta enviar o código por e-mail. Retorna True se enviou, False se falhou."""
    try:
        Notificador().enviar_email(
            email,
            "Código de Verificação — Oráculo Analista",
            f"<h3>Olá, {nome}</h3>"
            f"<p>Seu código de verificação é: <strong>{codigo}</strong></p>"
            "<p>Use este código para ativar sua conta.</p>",
        )
        return True
    except Exception as e:
        logger.warning(f"Falha ao enviar e-mail para {email}: {e}")
        return False


def _expunge_user(session, user: UserAnalise) -> UserAnalise:
    session.expunge(user)
    make_transient(user)
    return user


def cadastrar_usuario(
    name: str, whatsapp: str, email: str,
    password: str, profile_image, cargo_id: int,
) -> bool:
    with Session() as session:
        try:
            if session.query(UserAnalise).filter_by(email=email).first():
                st.error("E-mail já cadastrado.")
                return False

            image_path = _save_profile_image(profile_image, email)
            codigo     = _gerar_codigo()
            senha_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            user = UserAnalise(
                name=name, whatsapp=whatsapp, email=email,
                password=senha_hash, profile_image_path=image_path,
                verification_code=codigo, is_verified=False, cargo_id=cargo_id,
            )
            session.add(user)
            session.commit()  # salva ANTES de tentar o e-mail

            # Tenta enviar e-mail — não bloqueia o cadastro se falhar
            email_ok = _enviar_codigo(email, name, codigo)

            st.session_state.temp_email            = email
            st.session_state.verificacao_pos_login = False

            if email_ok:
                st.success("✅ Cadastro realizado! Verifique o código enviado por e-mail.")
            else:
                # Fallback: exibe o código diretamente na tela
                st.warning(
                    f"⚠️ Cadastro realizado, mas não foi possível enviar o e-mail. "
                    f"Use este código para verificar sua conta: **{codigo}**"
                )
            return True

        except Exception as e:
            session.rollback()
            st.error(f"Erro no cadastro: {e}")
            return False


def autenticar_usuario(email: str, password: str):
    with Session() as session:
        try:
            user = session.query(UserAnalise).filter_by(email=email).first()
            if not user:
                st.error("Credenciais inválidas ou conta não verificada.")
                return None
            if not user.is_verified:
                st.warning("Conta não verificada. Insira o código enviado por e-mail.")
                st.session_state.temp_email            = user.email
                st.session_state.verificacao_pos_login = True
                return None
            if user.password and bcrypt.checkpw(password.encode(), user.password.encode()):
                return _expunge_user(session, user)
            st.error("Credenciais inválidas.")
            return None
        except Exception as e:
            st.error(f"Erro ao autenticar: {e}")
            return None


def verificar_codigo(email: str, codigo: str) -> bool:
    with Session() as session:
        try:
            user = session.query(UserAnalise).filter_by(email=email).first()
            if not user or user.verification_code != codigo:
                st.error("Código incorreto.")
                return False

            user.is_verified       = True
            user.verification_code = None
            session.commit()
            session.refresh(user)
            _expunge_user(session, user)

            st.session_state.user              = user
            st.session_state.logged_in         = True
            st.session_state.codigo_confirmado = True
            st.session_state.temp_email        = None
            st.rerun()
            return True

        except Exception as e:
            session.rollback()
            st.error(f"Erro ao verificar código: {e}")
            return False


def reenviar_codigo(email: str) -> bool:
    with Session() as session:
        try:
            user = session.query(UserAnalise).filter_by(email=email).first()
            if not user:
                st.error("Usuário não encontrado.")
                return False
            novo_codigo            = _gerar_codigo()
            user.verification_code = novo_codigo
            session.commit()
            email_ok = _enviar_codigo(email, user.name, novo_codigo)
            if email_ok:
                st.success("Código reenviado! Verifique seu e-mail.")
            else:
                st.warning(f"⚠️ Não foi possível enviar o e-mail. Código: **{novo_codigo}**")
            return True
        except Exception as e:
            session.rollback()
            st.error(f"Erro ao reenviar: {e}")
            return False
