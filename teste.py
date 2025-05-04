import streamlit as st
import os
import string
import random
import requests
import bcrypt
from PIL import Image
from decouple import config
from streamlit_extras.colored_header import colored_header

from bd_oraculo_analista.models.user_analise import UserAnalise
from bd_oraculo_analista.models.cargo import Cargo
from bd_oraculo_analista.config.db_session import create_session
from analista import oraculo_analista

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey
from bd_oraculo_analista.models.model_base import ModelBase


# Config
DATABASE_URL = config("DATABASE_URL", default="mysql+pymysql://root:root@127.0.0.1:3306/db_oraculo_analista")
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA", default=None)
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)


def inicializar_cargos():
    session = create_session()
    try:
        nomes = ["Admin", "Cliente", "Parceiro"]
        existentes = {c.nome for c in session.query(Cargo).all()}
        novos = [Cargo(nome=nome) for nome in nomes if nome not in existentes]
        if novos:
            session.add_all(novos)
            session.commit()
            print("Cargos iniciais criados com sucesso.")
    except Exception as e:
        print(f"Erro ao criar cargos: {e}")
        session.rollback()
    finally:
        session.close()

# Utils
def gerar_codigo_verificacao(tamanho=6):
    return ''.join(random.choices(string.digits, k=tamanho))

def save_profile_image(image, user_email):
    filename = f"{user_email}_{random.randint(1000,9999)}.png"
    path = os.path.join(PROFILE_IMAGES_DIR, filename)
    with open(path, "wb") as f:
        f.write(image.getbuffer())
    return path

def send_to_make_webhook(data):
    if not WEBHOOK_CADASTRO_ANALISTA:
        st.error("Webhook não configurado.")
        return False
    try:
        r = requests.post(WEBHOOK_CADASTRO_ANALISTA, json=data)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Erro webhook: {e}")
        return False

# Cadastro
def cadastrar_usuario(name, whatsapp, email, password, profile_image, cargo_nome):
    session = create_session()
    try:
        if session.query(UserAnalise).filter_by(email=email).first():
            st.error("E-mail já cadastrado.")
            return False

        cargo = session.query(Cargo).filter_by(nome=cargo_nome).first()
        if not cargo:
            st.error("Cargo inválido.")
            return False

        image_path = save_profile_image(profile_image, email)
        codigo = gerar_codigo_verificacao()
        senha_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        novo = UserAnalise(
            name=name,
            whatsapp=whatsapp,
            email=email,
            password=senha_hash,
            profile_image_path=image_path,
            verification_code=codigo,
            is_verified=False,
            cargo_id=cargo.id
        )
        session.add(novo)
        session.commit()

        send_to_make_webhook({
            "name": name,
            "whatsapp": whatsapp,
            "email": email,
            "verification_code": codigo,
            "cargo": cargo_nome
        })
        st.session_state.temp_email = email
        st.success("Cadastro realizado. Verifique o código enviado.")
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar: {e}")
        session.rollback()
        return False
    finally:
        session.close()

# Verificação
def verificar_codigo(email, codigo):
    session = create_session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        if user and user.verification_code == codigo:
            user.is_verified = True
            user.verification_code = None
            session.commit()
            st.session_state.user = user
            st.session_state.logged_in = True
            st.session_state.codigo_confirmado = True
            st.session_state.temp_email = None
            st.rerun()
            return True
        st.error("Código incorreto.")
        return False
    finally:
        session.close()

# Login
def autenticar_usuario(email, password):
    session = create_session()
    try:
        user = session.query(UserAnalise).filter_by(email=email, is_verified=True).first()
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user
        st.error("Credenciais inválidas ou conta não verificada.")
        return None
    finally:
        session.close()

# Interface
def interface():
    st.sidebar.title("Oráculo Analista")
    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastrar"])

    if opcao == "Cadastrar":
        nome = st.sidebar.text_input("Nome")
        zap = st.sidebar.text_input("WhatsApp")
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")
        imagem = st.sidebar.file_uploader("Imagem de Perfil", type=["png", "jpg", "jpeg"])

        session = create_session()
        cargos = session.query(Cargo).all()
        cargo_opcoes = [c.nome for c in cargos]
        cargo_selecionado = st.sidebar.selectbox("Tipo de Usuário", cargo_opcoes)
        session.close()

        if st.sidebar.button("Cadastrar"):
            if all([nome, zap, email, senha, imagem, cargo_selecionado]):
                cadastrar_usuario(nome, zap, email, senha, imagem, cargo_selecionado)
            else:
                st.sidebar.error("Preencha todos os campos.")

    elif opcao == "Login":
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Entrar"):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.rerun()

    # Verificação de código separada
    if "temp_email" in st.session_state and not st.session_state.get("codigo_confirmado"):
        st.info("Digite o código de verificação enviado.")
        codigo = st.text_input("Código de Verificação")
        if st.button("Confirmar Código"):
            verificar_codigo(st.session_state.temp_email, codigo)

# Principal
def main():
    inicializar_cargos()
    if not st.session_state.get("logged_in"):
        interface()
    else:
        user = st.session_state.user
        st.sidebar.subheader(f"Bem-vindo(a), {user.name}")
        st.sidebar.image(user.profile_image_path, width=100)
        st.sidebar.write(f"Email: {user.email}")
        st.sidebar.write(f"WhatsApp: {user.whatsapp}")
        oraculo_analista()

if __name__ == "__main__":
    main()

