import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import string
import random
import requests
from PIL import Image
from streamlit_extras.colored_header import colored_header
from decouple import config
import bcrypt
from analista import oraculo_analista

# Configurações
DATABASE_URL = config("DATABASE_URL")
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

# Modelo
class UserAnalise(Base):
    __tablename__ = "user_analise"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image_path = Column(String(500), nullable=True)
    verification_code = Column(String(6), nullable=True)
    is_verified = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# Utilitários
def gerar_codigo_verificacao(tamanho=6):
    return ''.join(random.choices(string.digits, k=tamanho))

def save_profile_image(image, user_email):
    path = os.path.join(PROFILE_IMAGES_DIR, f"{user_email}.png")
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
def cadastrar_usuario(name, whatsapp, email, password, profile_image):
    session = Session()
    try:
        if session.query(UserAnalise).filter_by(email=email).first():
            st.error("E-mail já cadastrado.")
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
            is_verified=False
        )
        session.add(novo)
        session.commit()

        send_to_make_webhook({
            "name": name,
            "whatsapp": whatsapp,
            "email": email,
            "verification_code": codigo
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
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        if user and user.verification_code == codigo:
            user.is_verified = True
            user.verification_code = None
            session.commit()
            session.expunge(user)
            session.close()

            session2 = Session()
            user_fresh = session2.query(UserAnalise).filter_by(email=email).first()
            st.session_state.user = user_fresh
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
    session = Session()
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

        if st.sidebar.button("Cadastrar"):
            if all([nome, zap, email, senha, imagem]):
                cadastrar_usuario(nome, zap, email, senha, imagem)
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
