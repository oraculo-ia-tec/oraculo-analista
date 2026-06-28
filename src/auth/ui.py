# ============================================================
# src/auth/ui.py
# Interface Streamlit de autenticação — sidebar
# ============================================================
from __future__ import annotations

import os

import requests
import streamlit as st

from ..models.base import Session
from ..models.user import Cargo
from .service import (
    cadastrar_usuario, autenticar_usuario,
    verificar_codigo, reenviar_codigo,
)


def _bloco_verificacao_codigo() -> None:
    """Bloco do sidebar para digitar e confirmar o código."""
    email = st.session_state.get("temp_email", "")

    if st.session_state.get("verificacao_pos_login"):
        st.warning("Conta não verificada. Insira o código enviado por e-mail.")
        codigo = st.text_input("Código de Verificação", key="codigo_login")
        if st.button("Confirmar Código", key="confirmar_login"):
            verificar_codigo(email, codigo)
    else:
        st.info(f"Código enviado para {email}.")
        if st.button("Reenviar Código"):
            reenviar_codigo(email)
        codigo = st.text_input("Código de Verificação", key="codigo_cadastro")
        if st.button("Confirmar Código", key="confirmar_cadastro"):
            verificar_codigo(email, codigo)


def interface() -> None:
    """Sidebar completo de login/cadastro."""
    if st.session_state.get("logged_in"):
        return

    st.sidebar.title("Oráculo Analista")
    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastrar"])

    if opcao == "Cadastrar":
        nome   = st.sidebar.text_input("Nome")
        zap    = st.sidebar.text_input("WhatsApp")
        email  = st.sidebar.text_input("Email")
        senha  = st.sidebar.text_input("Senha", type="password")
        imagem = st.sidebar.file_uploader("Imagem de Perfil", type=["png", "jpg", "jpeg"])

        if imagem:
            st.sidebar.image(imagem, caption="Pré-visualização", width=150)

        cargos = []
        try:
            with Session() as session:
                cargos = [(c.id, c.nome) for c in session.query(Cargo).all()]
        except Exception as e:
            st.sidebar.error(f"Erro ao buscar cargos: {e}")

        cargo_opcoes  = {nome_c: id_ for id_, nome_c in cargos}
        default_index = next(
            (i for i, (_, n) in enumerate(cargos) if n.lower() == "cliente"), 0
        )

        if cargos:
            cargo_nome = st.sidebar.selectbox(
                "Cargo", list(cargo_opcoes.keys()), index=default_index
            )
            cargo_id = cargo_opcoes[cargo_nome]
        else:
            cargo_id = None

        if st.sidebar.button("Cadastrar"):
            if not all([nome, zap, email, senha]):
                st.sidebar.error("Preencha todos os campos obrigatórios.")
            elif not cargo_id:
                st.sidebar.error("Selecione um cargo.")
            else:
                cadastrar_usuario(nome, zap, email, senha, imagem, cargo_id)

    elif opcao == "Login":
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.user      = user
                st.session_state.logged_in = True
                st.rerun()

    if st.session_state.get("temp_email") and not st.session_state.get("codigo_confirmado"):
        with st.sidebar:
            _bloco_verificacao_codigo()
