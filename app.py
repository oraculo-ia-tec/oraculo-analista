import streamlit as st
import os
import string
import random
import requests
import bcrypt
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Boolean, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from decouple import config
from analista import oraculo_analista

# Configurações
DATABASE_URL = config("DATABASE_URL")
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class UserAdmin(Base):
    __tablename__ = "user_admin"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    cpf_cnpj = Column(String(20))
    email = Column(String(254), unique=True, nullable=False)
    whatsapp = Column(String(15))
    endereco = Column(String(255))
    cep = Column(String(10))
    bairro = Column(String(100))
    cidade = Column(String(100))
    username = Column(String(50))
    password = Column(String(128))
    image = Column(String(100))
    created_at = Column(String(50))
    created_time = Column(String(50))
    deleted_at = Column(String(50))
    deleted_time = Column(String(50))
    cargo_id = Column(BigInteger, ForeignKey("cargo.id"))
    decisao = Column(Boolean)
    culto_id = Column(BigInteger)
    estado_civil = Column(String(20))
    filhos = Column(Integer)

class Enquete(Base):
    __tablename__ = "enquete"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    titulo = Column(String(200))
    descricao = Column(String)
    data_inicio = Column(String)
    data_fim = Column(String)
    ativo = Column(Boolean)
    opcao1 = Column(String(200))
    opcao2 = Column(String(200))
    opcao3 = Column(String(200))
    opcao4 = Column(String(200))
    created_dt = Column(String)
    updated_dt = Column(String)
    cargo_id = Column(BigInteger, ForeignKey("cargo.id"))

class RespostaEnquete(Base):
    __tablename__ = "resposta_enquete"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resposta = Column(String(255))
    explicacao = Column(String)
    enquete_id = Column(BigInteger, ForeignKey("enquete.id"))
    usuario_id = Column(BigInteger, ForeignKey("user_analise.id"))

class DirecionadoEnquete(Base):
    __tablename__ = "direcionado_enquete"
    id = Column(Integer, primary_key=True, autoincrement=True)
    enquete_id = Column(BigInteger, ForeignKey("enquete.id"))
    cargo_id = Column(BigInteger, ForeignKey("cargo.id"))
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

# Modelo
class Cargo(Base):
    __tablename__ = "cargo"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)
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
    cargo_id = Column(BigInteger, ForeignKey("cargo.id"), nullable=False)

Base.metadata.create_all(engine)

# Confirma criação no console
print("✅ Tabelas sincronizadas com o banco de dados")

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
def cadastrar_usuario(name, whatsapp, email, password, profile_image, cargo_id):
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
            is_verified=False,
            cargo_id=cargo_id
        )
        session.add(novo)
        session.commit()

        send_to_make_webhook({
            "name": name,
            "whatsapp": whatsapp,
            "email": email,
            "verification_code": codigo,
            "cargo_id": cargo_id
        })
        st.session_state.temp_email = email
        st.session_state.verificacao_pos_login = False
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
        user = session.query(UserAnalise).filter_by(email=email).first()
        if user:
            if not user.is_verified:
                st.warning("Sua conta ainda não foi verificada. Por favor, insira o código de verificação enviado para seu e-mail.")
                st.session_state.temp_email = user.email
                st.session_state.verificacao_pos_login = True
                return None
            if user.password and bcrypt.checkpw(password.encode(), user.password.encode()):
                return user
        st.error("Credenciais inválidas ou conta não verificada.")
        return None
    finally:
        session.close()

# Interface
def interface():
    if st.session_state.get("logged_in"):
        return

    st.sidebar.title("Oráculo Analista")
    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastrar"])

    if opcao == "Cadastrar":
        nome = st.sidebar.text_input("Nome")
        zap = st.sidebar.text_input("WhatsApp")
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")
        imagem = st.sidebar.file_uploader("Imagem de Perfil", type=["png", "jpg", "jpeg"])
        if imagem:
            st.sidebar.image(imagem, caption="Pré-visualização", width=150)

        # Define cargo padrão (Cliente) automaticamente
        cargo_id = 2  # ID do cargo "Cliente" no banco

        if st.sidebar.button("Cadastrar"):
            if all([nome, zap, email, senha, imagem, cargo_id]):
                cadastrar_usuario(nome, zap, email, senha, imagem, cargo_id)
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

    if "temp_email" in st.session_state and not st.session_state.get("codigo_confirmado"):
        with st.sidebar:
            if st.session_state.get("verificacao_pos_login"):
                st.warning("Sua conta ainda não foi verificada. Por favor, insira o código de verificação enviado para seu e-mail.")
                codigo = st.text_input("Código de Verificação")
                if st.button("Confirmar Código"):
                    verificar_codigo(st.session_state.temp_email, codigo)
            else:
                st.info(f"Digite o código de verificação enviado para {st.session_state.temp_email}.")
                if st.button("Reenviar Código"):
                    session = Session()
                    user = session.query(UserAnalise).filter_by(email=st.session_state.temp_email).first()
                    if user:
                        user.verification_code = gerar_codigo_verificacao()
                        session.commit()
                        send_to_make_webhook({
                            "name": user.name,
                            "whatsapp": user.whatsapp,
                            "email": user.email,
                            "verification_code": user.verification_code,
                            "cargo_id": user.cargo_id
                        })
                        st.success("Código reenviado com sucesso!")
                    session.close()
                codigo = st.text_input("Código de Verificação")
                if st.button("Confirmar Código"):
                    verificar_codigo(st.session_state.temp_email, codigo)


# Principal

def main():
    if not st.session_state.get("logged_in"):
        interface()

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

        st.markdown(
            """<div class='titulo-principal'>🚀 Oráculo Analista: Transformando Dados em Decisões Estratégicas</div>""",
            unsafe_allow_html=True)

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
        VIDEO_PATH = config("VIDEO_PATH", default="src/video/oraculo-analista.mp4")
        if os.path.exists(VIDEO_PATH):
            with open(VIDEO_PATH, "rb") as video_file:
                st.sidebar.video(video_file.read())

        st.markdown("---")

        st.markdown("""
        <small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>
        """, unsafe_allow_html=True)


    else:
        user = st.session_state.user
        st.sidebar.subheader(f"Bem-vindo(a), {user.name}")
        if user.profile_image_path and os.path.exists(user.profile_image_path):
            st.sidebar.image(user.profile_image_path, width=100)
        else:
            st.sidebar.image("./src/img/usuario.jpg", width=100)
        st.sidebar.write(f"Email: {user.email}")
        st.sidebar.write(f"WhatsApp: {user.whatsapp}")

        # 🔐 Botão de logout
        if st.sidebar.button("🔓 Sair do sistema"):
            for key in [
                "user", "logged_in", "codigo_confirmado", "temp_email",
                "name", "email", "image", "primeiro_nome", "messages"
            ]:
                st.session_state.pop(key, None)
            st.experimental_set_query_params()  # limpa parâmetros da URL
            st.rerun()

        oraculo_analista()


if __name__ == "__main__":
    st.set_page_config(page_title="Oráculo Analista", page_icon="📊", layout="wide")
    main()
