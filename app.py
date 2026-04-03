import os
import random
import shutil
import string

import bcrypt
import requests
import streamlit as st
import sqlite3
from decouple import AutoConfig
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================
# Configurações
# =========================
config = AutoConfig()
DATABASE_URL = config("DATABASE_URL", default="sqlite:///oraculo_analista.db")
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA", default="")
VIDEO_PATH = config("VIDEO_PATH", default="src/video/oraculo-analista.mp4")

# No Streamlit Cloud o diretório /mount/src/ é read-only.
# Copia o banco para /tmp/ se necessário para permitir escrita.
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    _db_file = DATABASE_URL.replace("sqlite:///", "")
    _db_abs = os.path.abspath(_db_file)
    _db_dir = os.path.dirname(_db_abs)
    if os.path.exists(_db_abs) and not os.access(_db_dir, os.W_OK):
        _tmp_path = os.path.join("/tmp", os.path.basename(_db_abs))
        if not os.path.exists(_tmp_path):
            shutil.copy2(_db_abs, _tmp_path)
        DATABASE_URL = f"sqlite:///{_tmp_path}"

Base = declarative_base()

PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@st.cache_resource
def get_session_factory():
    return sessionmaker(bind=get_engine())


@st.cache_resource
def init_db():
    Base.metadata.create_all(get_engine())


@st.cache_data
def load_video(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# =========================
# Modelos
# =========================
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


init_db()
Session = get_session_factory()


# =========================
# Utilitários
# =========================
def gerar_codigo_verificacao(tamanho: int = 6) -> str:
    return "".join(random.choices(string.digits, k=tamanho))


def save_profile_image(image, user_email: str) -> str | None:
    if image is None:
        return None

    path = os.path.join(PROFILE_IMAGES_DIR, f"{user_email}.png")
    with open(path, "wb") as f:
        f.write(image.getbuffer())
    return path


def send_to_make_webhook(data: dict) -> bool:
    if not WEBHOOK_CADASTRO_ANALISTA:
        st.error("Webhook não configurado.")
        return False

    try:
        response = requests.post(
            WEBHOOK_CADASTRO_ANALISTA, json=data, timeout=20)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erro webhook: {e}")
        return False


# =========================
# Cadastro
# =========================
def cadastrar_usuario(name, whatsapp, email, password, profile_image, cargo_id):
    email = email.strip().lower()
    session = Session()
    try:
        usuario_existente = session.query(
            UserAnalise).filter_by(email=email).first()
        if usuario_existente:
            st.error("E-mail já cadastrado.")
            return False

        image_path = save_profile_image(profile_image, email)
        codigo = gerar_codigo_verificacao()
        senha_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()

        novo_usuario = UserAnalise(
            name=name,
            whatsapp=whatsapp,
            email=email,
            password=senha_hash,
            profile_image_path=image_path,
            verification_code=codigo,
            is_verified=False,
            cargo_id=cargo_id,
        )

        session.add(novo_usuario)
        session.commit()

        from notification import Notificador
        notificador = Notificador()

        assunto = "Código de Verificação - Oráculo Analista"
        mensagem = f"""
        <h3>Olá, {name}</h3>
        <p>Seu código de verificação para o Oráculo Analista é: <strong>{codigo}</strong></p>
        <p>Use este código para ativar sua conta.</p>
        """

        notificador.enviar_email(email, assunto, mensagem)

        st.session_state.temp_email = email
        st.session_state.verificacao_pos_login = False
        st.success("Cadastro realizado. Verifique o código enviado por e-mail.")
        return True

    except Exception as e:
        session.rollback()
        st.error(f"Erro no cadastro/envio do código: {e}")
        return False

    finally:
        session.close()


# =========================
# Verificação
# =========================
def verificar_codigo(email, codigo):
    email = email.strip().lower()
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()

        if user and user.verification_code == codigo:
            user.is_verified = True
            user.verification_code = None
            session.commit()

            session2 = Session()
            try:
                user_fresh = session2.query(
                    UserAnalise).filter_by(email=email).first()
                st.session_state.user_id = user_fresh.id
                st.session_state.logged_in = True
                st.session_state.codigo_confirmado = True
                st.session_state.temp_email = None
                st.rerun()
            finally:
                session2.close()

            return True

        st.error("Código incorreto.")
        return False
    finally:
        session.close()


# =========================
# Login
# =========================
def autenticar_usuario(email, password):
    email = email.strip().lower()
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()

        if user:
            if not user.is_verified:
                st.warning(
                    "Sua conta ainda não foi verificada. "
                    "Por favor, insira o código de verificação enviado para seu e-mail."
                )
                st.session_state.temp_email = user.email
                st.session_state.verificacao_pos_login = True
                return None

            if user.password and bcrypt.checkpw(password.encode(), user.password.encode()):
                return user

            st.error("Senha incorreta.")
            return None

        st.error("E-mail não encontrado.")
        return None
    finally:
        session.close()


# =========================
# Interface de autenticação
# =========================
def interface():
    if st.session_state.get("logged_in"):
        return

    st.sidebar.title("Oráculo Analista")
    menu_opcoes = ["Login", "Cadastrar"]
    opcao = st.sidebar.radio("Selecione:", menu_opcoes)

    # Limpar estado de verificação ao trocar de aba
    if "ultimo_opcao" not in st.session_state:
        st.session_state.ultimo_opcao = opcao
    if st.session_state.ultimo_opcao != opcao:
        for k in ["temp_email", "verificacao_pos_login", "codigo_confirmado"]:
            st.session_state.pop(k, None)
        st.session_state.ultimo_opcao = opcao

    if opcao == "Cadastrar":
        nome = st.sidebar.text_input("Nome")
        zap = st.sidebar.text_input("WhatsApp")
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")
        imagem = st.sidebar.file_uploader(
            "Imagem de Perfil", type=["png", "jpg", "jpeg"])

        if imagem:
            st.sidebar.image(imagem, caption="Pré-visualização", width=150)

        # Cargo fixo: Cliente (cadastro público)
        cargo_id = None
        try:
            _db_path = DATABASE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cargo WHERE nome = 'Cliente'")
            row = cursor.fetchone()
            if row:
                cargo_id = row[0]
            conn.close()
        except Exception as e:
            st.sidebar.error(f"Erro ao buscar cargo: {e}")

        if st.sidebar.button("Cadastrar"):
            if not nome or not zap or not email or not senha:
                st.sidebar.error("Preencha todos os campos obrigatórios.")
            elif not cargo_id:
                st.sidebar.error("Cargo 'Cliente' não encontrado no banco.")
            else:
                cadastrar_usuario(
                    name=nome,
                    whatsapp=zap,
                    email=email,
                    password=senha,
                    profile_image=imagem,
                    cargo_id=cargo_id,
                )

    elif opcao == "Login":
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Entrar"):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.user_id = user.id
                st.session_state.logged_in = True
                st.rerun()

    if "temp_email" in st.session_state and not st.session_state.get("codigo_confirmado"):
        with st.sidebar:
            if st.session_state.get("verificacao_pos_login"):
                st.warning(
                    "Sua conta ainda não foi verificada. "
                    "Por favor, insira o código de verificação enviado para seu e-mail."
                )
                if st.button("Reenviar Código", key="reenviar_codigo_login"):
                    session = Session()
                    try:
                        user = session.query(UserAnalise).filter_by(
                            email=st.session_state.temp_email
                        ).first()

                        if not user:
                            st.error(
                                "Usuário não encontrado para reenvio do código.")
                        else:
                            novo_codigo = gerar_codigo_verificacao()
                            user.verification_code = novo_codigo
                            session.commit()

                            from notification import Notificador
                            notificador = Notificador()

                            assunto = "Código de Verificação - Oráculo Analista"
                            mensagem = f"""
                            <h3>Olá, {user.name}</h3>
                            <p>Seu novo código de verificação é: <strong>{novo_codigo}</strong></p>
                            <p>Use este código para ativar sua conta.</p>
                            """

                            notificador.enviar_email(
                                user.email, assunto, mensagem)
                            st.success(
                                "Código reenviado com sucesso! Verifique seu e-mail.")

                    except Exception as e:
                        session.rollback()
                        st.error(
                            f"Erro ao reenviar e-mail de verificação: {e}")

                    finally:
                        session.close()

                codigo = st.text_input(
                    "Código de Verificação", key="codigo_login")
                if st.button("Confirmar Código", key="confirmar_codigo_login"):
                    verificar_codigo(st.session_state.temp_email, codigo)
            else:
                st.info(
                    f"Digite o código de verificação enviado para {st.session_state.temp_email}.")
                if st.button("Reenviar Código"):
                    session = Session()
                    try:
                        user = session.query(UserAnalise).filter_by(
                            email=st.session_state.temp_email
                        ).first()

                        if not user:
                            st.error(
                                "Usuário não encontrado para reenvio do código.")
                        else:
                            novo_codigo = gerar_codigo_verificacao()
                            user.verification_code = novo_codigo
                            session.commit()

                            from notification import Notificador
                            notificador = Notificador()

                            assunto = "Código de Verificação - Oráculo Analista"
                            mensagem = f"""
                            <h3>Olá, {user.name}</h3>
                            <p>Seu novo código de verificação é: <strong>{novo_codigo}</strong></p>
                            <p>Use este código para ativar sua conta.</p>
                            """

                            notificador.enviar_email(
                                user.email, assunto, mensagem)
                            st.success(
                                "Código reenviado com sucesso! Verifique seu e-mail.")

                    except Exception as e:
                        session.rollback()
                        st.error(
                            f"Erro ao reenviar e-mail de verificação: {e}")

                    finally:
                        session.close()

                codigo = st.text_input(
                    "Código de Verificação", key="codigo_cadastro")
                if st.button("Confirmar Código", key="confirmar_codigo_cadastro"):
                    session = Session()
                    try:
                        user = session.query(UserAnalise).filter_by(
                            email=st.session_state.temp_email
                        ).first()

                        if not user:
                            st.error("Usuário não encontrado.")
                        elif codigo != user.verification_code:
                            st.error("Código de verificação inválido.")
                        else:
                            user.is_verified = True
                            user.verification_code = None
                            session.commit()

                            session2 = Session()
                            try:
                                user_fresh = session2.query(
                                    UserAnalise).filter_by(email=st.session_state.temp_email).first()
                                st.session_state.user_id = user_fresh.id
                                st.session_state.logged_in = True
                                st.session_state.codigo_confirmado = True
                                st.session_state.temp_email = None
                                st.rerun()
                            finally:
                                session2.close()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao confirmar código: {e}")
                    finally:
                        session.close()

    if "verificar_pagamento" not in st.session_state:
        st.session_state.verificar_pagamento = False

    if st.session_state.verificar_pagamento:
        st.markdown("### 🔒 Verificação de Pagamento do Plano")
        email_verificacao = st.text_input(
            "Digite seu e-mail de cadastro:", key="email_verif")

        if st.button("Verificar Status de Pagamento"):
            try:
                response = requests.get(
                    "http://localhost:8000/verificar-pagamento",
                    params={"email": email_verificacao},
                    timeout=20,
                )

                if response.status_code == 200:
                    dados = response.json()
                    if dados["status"] == "confirmado":
                        st.success(
                            "✅ Pagamento confirmado! Código de verificação:")
                        st.code(dados["codigo_verificacao"])
                    else:
                        st.warning(dados["mensagem"])
                else:
                    st.error("❌ Não foi possível verificar o pagamento.")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")


# =========================
# Landing / principal
# =========================
def main():
    if not st.session_state.get("logged_in"):
        interface()

        st.markdown(
            """
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
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='titulo-principal'>🚀 Oráculo Analista: Transformando Dados em Decisões Estratégicas</div>",
            unsafe_allow_html=True,
        )

        if os.path.exists("./src/img/oraculo-analista.jpg"):
            st.image("./src/img/oraculo-analista.jpg", width=700)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                "<div class='subtitulo'>📈 Aumento da Competitividade</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Análises ultrarrápidas que colocam sua empresa à frente do mercado<br>
                - Decisões estratégicas baseadas em dados concretos e confiáveis<br>
                - Vantagem competitiva real para crescer com segurança
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                "<div class='subtitulo'>🎯 Objetivo: Análises Precisas</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Extraia inteligência de documentos complexos com facilidade<br>
                - Compreensão de dados vitais para acelerar estratégias<br>
                - Menos achismo, mais assertividade nas decisões
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        col3, col4 = st.columns(2)
        with col3:
            st.markdown(
                "<div class='subtitulo'>🧠 Descomplicação de Dados Complexos</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Interface amigável para empresários<br>
                - Informações transformadas em ações claras e aplicáveis<br>
                - Inteligência de dados acessível sem precisar ser técnico
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                "<div class='subtitulo'>⚡ Agilidade na Tomada de Decisões</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Processamento rápido que responde no ritmo do seu negócio<br>
                - Reduza o tempo entre problema e solução<br>
                - Tome decisões urgentes com segurança e suporte confiável
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        col5, col6 = st.columns(2)
        with col5:
            st.markdown(
                "<div class='subtitulo'>🌱 Sustentabilidade e Ética</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Uso ético e inteligente dos dados<br>
                - Alinhamento com práticas empresariais sustentáveis<br>
                - Contribuição para decisões com impacto positivo a longo prazo
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col6:
            st.markdown(
                "<div class='subtitulo'>💼 Para Líderes Estratégicos</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class='descricao-gradient'>
                - Ferramenta desenvolvida para CEOs, diretores e tomadores de decisão<br>
                - Otimize fluxos e melhore reuniões com insights automáticos<br>
                - Capacite sua liderança com inteligência preditiva
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            "<div class='subtitulo'>✅ Resumo e Próximos Passos</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='descricao-gradient'>
            - Transforme dados brutos em <strong>inteligência acionável</strong><br>
            - Capacite sua empresa a reagir com agilidade e precisão<br>
            - Posicione sua marca no topo com o <strong>Oráculo Analista</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            "<div class='subtitulo'>▶️ Apresentação em Vídeo</div>", unsafe_allow_html=True)

        if os.path.exists(VIDEO_PATH):
            st.sidebar.video(load_video(VIDEO_PATH))

        st.markdown("---")
        st.markdown(
            "<small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>",
            unsafe_allow_html=True,
        )

    else:
        # Recarregar usuário em sessão ativa usando o ID salvo
        session = Session()
        try:
            user = session.query(UserAnalise).get(st.session_state.user_id)
            if not user:
                st.error("Usuário não encontrado.")
                st.session_state.clear()
                st.rerun()
            # Guardar atributos antes de fechar a sessão
            user_id = user.id
            user_name = user.name
            user_email = user.email
            user_whatsapp = user.whatsapp
            user_cargo_id = user.cargo_id
            user_profile_image = user.profile_image_path

            cargo = session.query(Cargo).filter_by(id=user_cargo_id).first()
            cargo_nome = cargo.nome if cargo else "Cliente"
        finally:
            session.close()

        # Salvar dados do usuário para uso no chat
        st.session_state.primeiro_nome = user_name.split()[0] if user_name else "Usuário"
        st.session_state.user_profile_image = user_profile_image

        # Permissões por cargo
        from views.permissoes import obter_paginas_por_cargo
        paginas_permitidas = obter_paginas_por_cargo(cargo_nome)

        st.sidebar.subheader(f"Bem-vindo(a), {user_name}")

        if user_profile_image and os.path.exists(user_profile_image):
            st.sidebar.image(user_profile_image, width=100)
        elif os.path.exists("./src/img/usuario.jpg"):
            st.sidebar.image("./src/img/usuario.jpg", width=100)

        st.sidebar.write(f"Email: {user_email}")
        st.sidebar.write(f"WhatsApp: {user_whatsapp}")
        st.sidebar.caption(f"Cargo: {cargo_nome}")

        # Menu de navegação
        st.sidebar.markdown("---")
        pagina = st.sidebar.radio("Navegação", paginas_permitidas)

        st.sidebar.markdown("---")
        if st.sidebar.button("🔓 Sair do sistema"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Roteamento de páginas
        if pagina == "Oráculo Analista":
            from analista import oraculo_analista
            oraculo_analista()
        elif pagina == "Dashboard":
            from views.dashboard import render_dashboard
            render_dashboard(Session, UserAnalise, Cargo)
        elif pagina == "Clientes":
            from views.clientes import render_clientes
            render_clientes(Session, UserAnalise, Cargo)
        elif pagina == "Parceiros":
            from views.parceiros import render_parceiros
            render_parceiros(Session, UserAnalise, Cargo)
        elif pagina == "Financeiro":
            from views.financeiro import render_financeiro
            render_financeiro(Session, UserAnalise, Cargo)
        elif pagina == "Configuração":
            from views.configuracao import render_configuracao
            render_configuracao(Session, UserAnalise, Cargo)


if __name__ == "__main__":
    st.set_page_config(page_title="Oráculo Analista",
                       page_icon="📊", layout="wide")
    main()
