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
from analista import oraculo_analista, configurar_usuario_logado


st.set_page_config(page_title="Oráculo Analista - Apresentação", layout="wide")

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
        configurar_usuario_logado(novo)
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
            configurar_usuario_logado(user_fresh)
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
                configurar_usuario_logado(user)
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

        if st.sidebar.button("Logout"):
            for key in ["user", "logged_in", "codigo_confirmado", "temp_email", "name", "email", "image", "primeiro_nome", "messages"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_set_query_params()  # limpa parâmetros de URL
            st.rerun()

        oraculo_analista()

if __name__ == "__main__":
    main()


# Estilo personalizado para o título e conteúdo
st.markdown("""
    <style>
    .titulo-principal {
        font-size: 3rem;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subtitulo {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
    }
    .descricao-gradient {
        font-size: 1.1rem;
        background: -webkit-linear-gradient(45deg, violet, white);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class='titulo-principal'>🚀 Oráculo Analista: Transformando Dados em Decisões Estratégicas</div>""", unsafe_allow_html=True)

# Imagem representativa
st.image("./src/img/oraculo-analista.jpg", width=700)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='subtitulo'>📈 Aumento da Competitividade</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Análises ultrarrápidas que colocam sua empresa à frente do mercado<br>
    - Decisões estratégicas baseadas em dados concretos e confiáveis<br>
    - Vantagem competitiva real para crescer com segurança
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<div class='subtitulo'>🎯 Objetivo: Análises Precisas</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Extraia inteligência de documentos complexos com facilidade<br>
    - Compreensão de dados vitais para acelerar estratégias<br>
    - Menos achismo, mais assertividade nas decisões
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.markdown("<div class='subtitulo'>🧠 Descomplicação de Dados Complexos</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Interface amigável para empresários<br>
    - Informações transformadas em ações claras e aplicáveis<br>
    - Inteligência de dados acessível sem precisar ser técnico
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("<div class='subtitulo'>⚡ Agilidade na Tomada de Decisões</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Processamento rápido que responde no ritmo do seu negócio<br>
    - Reduza o tempo entre problema e solução<br>
    - Tome decisões urgentes com segurança e suporte confiável
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

col5, col6 = st.columns(2)
with col5:
    st.markdown("<div class='subtitulo'>🌱 Sustentabilidade e Ética</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Uso ético e inteligente dos dados<br>
    - Alinhamento com práticas empresariais sustentáveis<br>
    - Contribuição para decisões com impacto positivo a longo prazo
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("<div class='subtitulo'>💼 Para Líderes Estratégicos</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='descricao-gradient'>
    - Ferramenta desenvolvida para CEOs, diretores e tomadores de decisão<br>
    - Otimize fluxos e melhore reuniões com insights automáticos<br>
    - Capacite sua liderança com inteligência preditiva
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Resumo final
st.markdown("<div class='subtitulo'>✅ Resumo e Próximos Passos</div>", unsafe_allow_html=True)
st.markdown("""
<div class='descricao-gradient'>
- Transforme dados brutos em <strong>inteligência acionável</strong><br>
- Capacite sua empresa a reagir com agilidade e precisão<br>
- Posicione sua marca no topo com o <strong>Oráculo Analista</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Apresentar vídeo
st.markdown("<div class='subtitulo'>▶️ Apresentação em Vídeo</div>", unsafe_allow_html=True)
st.video("./src/video/oraculosia-apresentacao.mp4")  # Substitua com o link real do vídeo  # Substitua com o link real do vídeo

st.markdown("---")

st.markdown("""
<small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>
""", unsafe_allow_html=True)

