import os
import random
import secrets
import string
from datetime import datetime, timedelta

import bcrypt
import requests
import streamlit as st
from decouple import AutoConfig
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


from notification import Notificador
from analista import oraculo_analista


# =========================
# Configurações
# =========================
config = AutoConfig()
DATABASE_URL = config("DATABASE_URL", default="sqlite:///oraculo.db")
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA", default="")
VIDEO_PATH = config("VIDEO_PATH", default="src/video/oraculo-analista.mp4")
APP_BASE_URL = config("APP_BASE_URL", default="https://oraculo-analista.streamlit.app")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

# Expiração do token de reset: 60 minutos
RESET_TOKEN_EXPIRY_MINUTES = 60


# =========================
# Modelos
# =========================
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
    # Campos para recuperação de senha
    reset_token = Column(String(128), nullable=True)
    reset_token_expiry = Column(String(50), nullable=True)


Base.metadata.create_all(engine)


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
# Recuperação de senha
# =========================
def solicitar_recuperacao_senha(email: str) -> bool:
    """Gera token seguro, persiste no banco e envia e-mail com link."""
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        # Resposta genérica por segurança (não revela se e-mail existe)
        if not user:
            return True

        token = secrets.token_urlsafe(48)
        expiry = (datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)).isoformat()

        user.reset_token = token
        user.reset_token_expiry = expiry
        session.commit()

        link = f"{APP_BASE_URL}?reset_token={token}"

        notificador = Notificador()
        notificador.enviar_recuperacao_senha(
            nome=user.name,
            email=user.email,
            link=link,
        )
        return True

    except Exception as e:
        session.rollback()
        st.error(f"Erro ao solicitar recuperação de senha: {e}")
        return False
    finally:
        session.close()


def validar_reset_token(token: str):
    """Retorna o usuário se o token for válido e não expirado, senão None."""
    if not token:
        return None
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(reset_token=token).first()
        if not user or not user.reset_token_expiry:
            return None
        expiry = datetime.fromisoformat(user.reset_token_expiry)
        if datetime.utcnow() > expiry:
            return None
        return user
    finally:
        session.close()


def redefinir_senha_e_verificar(token: str, nova_senha: str) -> bool:
    """
    Redefine a senha do usuário e envia código de verificação por e-mail.
    O usuário só acessa o sistema após confirmar o código.
    """
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(reset_token=token).first()
        if not user or not user.reset_token_expiry:
            st.error("Token inválido.")
            return False

        expiry = datetime.fromisoformat(user.reset_token_expiry)
        if datetime.utcnow() > expiry:
            st.error("Este link expirou. Solicite um novo.")
            return False

        # Atualiza a senha
        senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
        user.password = senha_hash

        # Gera código de verificação para confirmar acesso
        codigo = gerar_codigo_verificacao()
        user.verification_code = codigo
        user.is_verified = False

        # Invalida o token de reset
        user.reset_token = None
        user.reset_token_expiry = None

        session.commit()

        notificador = Notificador()
        # Notifica que a senha foi alterada
        notificador.enviar_senha_alterada(nome=user.name, email=user.email)
        # Envia código de verificação para acessar o sistema
        notificador.enviar_verificacao(
            nome=user.name,
            email=user.email,
            codigo=codigo,
        )

        # Prepara session_state para etapa de verificação
        st.session_state.temp_email = user.email
        st.session_state.verificacao_pos_login = True
        st.session_state.reset_token = None
        st.session_state.tela = "verificacao"
        return True

    except Exception as e:
        session.rollback()
        st.error(f"Erro ao redefinir senha: {e}")
        return False
    finally:
        session.close()


# =========================
# Tela: Esqueci minha senha
# =========================
def tela_esqueci_senha():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 Recuperar Senha")
    st.sidebar.caption("Informe seu e-mail cadastrado para receber o link de redefinição.")

    email_reset = st.sidebar.text_input("E-mail cadastrado", key="email_reset_input")

    col_voltar, col_enviar = st.sidebar.columns(2)
    with col_voltar:
        if st.button("← Voltar", key="btn_voltar_reset", use_container_width=True):
            st.session_state.tela = "login"
            st.rerun()
    with col_enviar:
        if st.button("Enviar link", key="btn_enviar_reset", type="primary", use_container_width=True):
            if not email_reset or "@" not in email_reset:
                st.sidebar.error("Informe um e-mail válido.")
            else:
                with st.sidebar:
                    with st.spinner("Enviando..."):
                        solicitar_recuperacao_senha(email_reset)
                st.sidebar.success(
                    "✅ Se este e-mail estiver cadastrado, você receberá o link em instantes. "
                    "Verifique também a pasta de spam."
                )


# =========================
# Tela: Criar nova senha (via token na URL)
# =========================
def tela_nova_senha(token: str):
    st.markdown(
        """
        <style>
        .reset-container {
            max-width: 480px;
            margin: 60px auto;
            background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #3a1f6e;
            border-radius: 16px;
            padding: 48px 40px;
            text-align: center;
        }
        .reset-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
        }
        .reset-sub {
            font-size: 1rem;
            color: #b0aac8;
            margin-bottom: 32px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user = validar_reset_token(token)

    if not user:
        st.error("❌ Link inválido ou expirado. Solicite um novo na tela de login.")
        if st.button("← Voltar ao login"):
            st.query_params.clear()
            st.rerun()
        return

    st.markdown(
        f"""
        <div class='reset-container'>
            <div class='reset-title'>🔐 Criar Nova Senha</div>
            <div class='reset-sub'>Olá, <strong style='color:#a855f7'>{user.name.split()[0]}</strong>!
            Defina sua nova senha de acesso ao Oráculo Analista.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_nova_senha", clear_on_submit=False):
        nova_senha = st.text_input(
            "Nova senha",
            type="password",
            placeholder="Mínimo 8 caracteres",
            help="Use letras maiúsculas, minúsculas, números e símbolos.",
        )
        confirmar_senha = st.text_input(
            "Confirmar nova senha",
            type="password",
            placeholder="Repita a senha",
        )
        salvar = st.form_submit_button("💾 Salvar nova senha", type="primary", use_container_width=True)

        if salvar:
            if not nova_senha or len(nova_senha) < 8:
                st.error("A senha deve ter pelo menos 8 caracteres.")
            elif nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                with st.spinner("Salvando..."):
                    ok = redefinir_senha_e_verificar(token, nova_senha)
                if ok:
                    st.success(
                        "✅ Senha salva! Enviamos um código de verificação para o seu e-mail. "
                        "Insira-o na barra lateral para acessar o sistema."
                    )
                    st.query_params.clear()
                    st.rerun()


# =========================
# Cadastro
# =========================
def cadastrar_usuario(name, whatsapp, email, password, profile_image, cargo_id):
    session = Session()
    try:
        usuario_existente = session.query(UserAnalise).filter_by(email=email).first()
        if usuario_existente:
            st.error("E-mail já cadastrado.")
            return False

        image_path = save_profile_image(profile_image, email)
        codigo = gerar_codigo_verificacao()
        senha_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

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

        notificador = Notificador()
        notificador.enviar_boas_vindas(
            nome=name,
            email=email,
            whatsapp=whatsapp,
        )
        notificador.enviar_verificacao(nome=name, email=email, codigo=codigo)

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
                st.session_state.user = user_fresh
                st.session_state.logged_in = True
                st.session_state.codigo_confirmado = True
                st.session_state.temp_email = None
                st.session_state.tela = "login"
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

        st.error("Credenciais inválidas ou conta não verificada.")
        return None
    finally:
        session.close()


# =========================
# Interface de autenticação
# =========================
def interface():
    if st.session_state.get("logged_in"):
        return

    # Inicializa tela padrão
    if "tela" not in st.session_state:
        st.session_state.tela = "login"

    st.sidebar.title("Oráculo Analista")

    # --- Tela: Esqueci minha senha ---
    if st.session_state.tela == "esqueci_senha":
        tela_esqueci_senha()
        return

    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastrar"])

    if opcao == "Cadastrar":
        nome = st.sidebar.text_input("Nome")
        zap = st.sidebar.text_input("WhatsApp")
        email = st.sidebar.text_input("Email")
        senha = st.sidebar.text_input("Senha", type="password")
        imagem = st.sidebar.file_uploader(
            "Imagem de Perfil", type=["png", "jpg", "jpeg"])

        if imagem:
            st.sidebar.image(imagem, caption="Pré-visualização", width=150)

        # Buscar cargos do banco
        import sqlite3
        cargos = []
        try:
            conn = sqlite3.connect('oraculo_analista.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM cargo")
            cargos = cursor.fetchall()
            conn.close()
        except Exception as e:
            st.sidebar.error(f"Erro ao buscar cargos: {e}")

        cargo_opcoes = {nome: id_ for id_, nome in cargos}
        default_index = 0
        if cargos:
            for idx, (id_, nome) in enumerate(cargos):
                if nome.lower() == "cliente":
                    default_index = idx
                    break
            cargo_nome = st.sidebar.selectbox("Cargo", list(
                cargo_opcoes.keys()), index=default_index)
            cargo_id = cargo_opcoes[cargo_nome]
        else:
            cargo_nome = None
            cargo_id = None

        if st.sidebar.button("Cadastrar"):
            if not nome or not zap or not email or not senha:
                st.sidebar.error("Preencha todos os campos obrigatórios.")
            elif not cargo_id:
                st.sidebar.error("Selecione um cargo.")
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

        # Botões lado a lado: Entrar | Esqueci minha senha
        col_entrar, col_esqueci = st.sidebar.columns([1, 1])
        with col_entrar:
            entrar = st.button("▶ Entrar", key="btn_entrar", type="primary", use_container_width=True)
        with col_esqueci:
            esqueci = st.button("🔑 Esqueci a senha", key="btn_esqueci", use_container_width=True)

        if entrar:
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.rerun()

        if esqueci:
            st.session_state.tela = "esqueci_senha"
            st.rerun()

    if "temp_email" in st.session_state and not st.session_state.get("codigo_confirmado"):
        with st.sidebar:
            if st.session_state.get("verificacao_pos_login"):
                st.warning(
                    "Sua conta ainda não foi verificada. "
                    "Por favor, insira o código de verificação enviado para seu e-mail."
                )
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
                            st.error("Usuário não encontrado para reenvio do código.")
                        else:
                            novo_codigo = gerar_codigo_verificacao()
                            user.verification_code = novo_codigo
                            session.commit()

                            notificador = Notificador()
                            notificador.enviar_verificacao(
                                nome=user.name,
                                email=user.email,
                                codigo=novo_codigo,
                            )
                            st.success("Código reenviado com sucesso! Verifique seu e-mail.")

                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao reenviar e-mail de verificação: {e}")

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
                            st.success("Conta verificada com sucesso!")
                            st.session_state.temp_email = None
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
    # Detecta token de reset na URL (?reset_token=...)
    params = st.query_params
    reset_token = params.get("reset_token", None)

    if reset_token:
        tela_nova_senha(reset_token)
        return

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
            with open(VIDEO_PATH, "rb") as video_file:
                st.sidebar.video(video_file.read())

        st.markdown("---")
        st.markdown(
            "<small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>",
            unsafe_allow_html=True,
        )

    else:
        user = st.session_state.user
        st.sidebar.subheader(f"Bem-vindo(a), {user.name}")

        if user.profile_image_path and os.path.exists(user.profile_image_path):
            st.sidebar.image(user.profile_image_path, width=100)
        elif os.path.exists("./src/img/usuario.jpg"):
            st.sidebar.image("./src/img/usuario.jpg", width=100)

        st.sidebar.write(f"Email: {user.email}")
        st.sidebar.write(f"WhatsApp: {user.whatsapp}")

        if st.sidebar.button("🔓 Sair do sistema"):
            for key in [
                "user",
                "logged_in",
                "codigo_confirmado",
                "temp_email",
                "tela",
                "name",
                "email",
                "image",
                "primeiro_nome",
                "messages",
                "full_content",
            ]:
                st.session_state.pop(key, None)

            st.rerun()

        oraculo_analista()


if __name__ == "__main__":
    st.set_page_config(page_title="Oráculo Analista",
                       page_icon="📊", layout="wide")
    main()
