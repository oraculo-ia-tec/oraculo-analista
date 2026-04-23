import logging
import os
import random
import string
import threading
import time

import bcrypt
import requests
import streamlit as st
from decouple import AutoConfig
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from notification import Notificador
from analista import oraculo_analista
from password_reset import (
    register_model as _register_password_reset_model,
    criar_token_para,
    validar_token,
    consumir_token,
    atualizar_senha,
)

LOGGER = logging.getLogger(__name__)


# =========================
# Configurações
# =========================
config = AutoConfig()


def is_streamlit_cloud() -> bool:
    return os.getenv('STREAMLIT_SHARING_MODE') == 'streamlit_app'


def get_setting(key: str, default=None):
    """Lê .env em ambiente local e st.secrets no Streamlit Cloud."""
    if is_streamlit_cloud():
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass

        return default

    try:
        value = config(key, default=None)
        if value is not None:
            return value
    except Exception:
        pass

    return os.getenv(key, default)


DATABASE_URL = get_setting('DATABASE_URL', 'sqlite:///oraculo_analista.db')
WEBHOOK_CADASTRO_ANALISTA = get_setting(
    'WEBHOOK_CADASTRO_ANALISTA', default='')
VIDEO_PATH = get_setting(
    'VIDEO_PATH', default='src/video/oraculo-analista.mp4')

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if str(
        DATABASE_URL).startswith('sqlite') else {},
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

PROFILE_IMAGES_DIR = './user_profiles/'
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)


# =========================
# Modelos
# =========================
class UserAdmin(Base):
    __tablename__ = 'user_admin'

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
    cargo_id = Column(BigInteger, ForeignKey('cargo.id'))
    decisao = Column(Boolean)
    culto_id = Column(BigInteger)
    estado_civil = Column(String(20))
    filhos = Column(Integer)


class Enquete(Base):
    __tablename__ = 'enquete'

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
    cargo_id = Column(BigInteger, ForeignKey('cargo.id'))


class RespostaEnquete(Base):
    __tablename__ = 'resposta_enquete'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resposta = Column(String(255))
    explicacao = Column(String)
    enquete_id = Column(BigInteger, ForeignKey('enquete.id'))
    usuario_id = Column(BigInteger, ForeignKey('user_analise.id'))


class DirecionadoEnquete(Base):
    __tablename__ = 'direcionado_enquete'

    id = Column(Integer, primary_key=True, autoincrement=True)
    enquete_id = Column(BigInteger, ForeignKey('enquete.id'))
    cargo_id = Column(BigInteger, ForeignKey('cargo.id'))


class Cargo(Base):
    __tablename__ = 'cargo'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)


class UserAnalise(Base):
    __tablename__ = 'user_analise'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image_path = Column(String(500), nullable=True)
    verification_code = Column(String(6), nullable=True)
    is_verified = Column(Boolean, default=False)
    cargo_id = Column(BigInteger, ForeignKey('cargo.id'), nullable=False)


PasswordReset = _register_password_reset_model(Base)

Base.metadata.create_all(engine)


# =========================
# Utilitários
# =========================
def gerar_codigo_verificacao(tamanho: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=tamanho))


def normalize_email(value: str) -> str:
    value = (value or '').strip()
    if value.startswith('[') and 'mailto:' in value:
        try:
            value = value.split('mailto:', 1)[1].split(')', 1)[0]
        except Exception:
            pass
    return value.lower()


def save_profile_image(image, user_email: str) -> str | None:
    if image is None:
        return None

    safe_email = normalize_email(user_email).replace(
        '/', '_').replace('\\', '_')
    path = os.path.join(PROFILE_IMAGES_DIR, f'{safe_email}.png')
    with open(path, 'wb') as f:
        f.write(image.getbuffer())
    return path


def send_to_make_webhook(data: dict) -> bool:
    if not WEBHOOK_CADASTRO_ANALISTA:
        st.error('Webhook não configurado.')
        return False

    try:
        response = requests.post(
            WEBHOOK_CADASTRO_ANALISTA, json=data, timeout=20)
        return response.status_code == 200
    except Exception as e:
        st.error(f'Erro webhook: {e}')
        return False


def _enviar_sequencia_emails(name: str, whatsapp: str, email: str, codigo: str, cargo_nome: str):
    """
    Executa em background:
      1. E-mail de boas-vindas (imediato)
      2. Aguarda 20 segundos
      3. E-mail de verificação com código
    """
    try:
        notificador = Notificador()
        notificador.enviar_boas_vindas(name, email, whatsapp, cargo=cargo_nome)
        LOGGER.info('E-mail de boas-vindas enviado para %s', email)
    except Exception as exc:
        LOGGER.error('Falha no e-mail de boas-vindas para %s: %s', email, exc)

    time.sleep(20)

    try:
        notificador = Notificador()
        notificador.enviar_verificacao(name, email, codigo)
        LOGGER.info('E-mail de verificação enviado para %s', email)
    except Exception as exc:
        LOGGER.error('Falha no e-mail de verificação para %s: %s', email, exc)


# =========================
# Cadastro
# =========================
def cadastrar_usuario(name, whatsapp, email, password, profile_image, cargo_id):
    session = Session()
    try:
        email = normalize_email(email)

        if session.query(UserAnalise).filter_by(email=email).first():
            st.error('E-mail já cadastrado.')
            return False

        image_path = save_profile_image(profile_image, email)
        codigo = gerar_codigo_verificacao()
        senha_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()

        novo = UserAnalise(
            name=name.strip(),
            whatsapp=whatsapp.strip(),
            email=email,
            password=senha_hash,
            profile_image_path=image_path,
            verification_code=codigo,
            is_verified=False,
            cargo_id=cargo_id,
        )

        session.add(novo)
        session.commit()

        # Resolve o nome do cargo para exibir no e-mail
        cargo_nome = 'Cliente'
        session_cargo = Session()
        try:
            cargo_obj = session_cargo.query(Cargo).filter_by(id=cargo_id).first()
            if cargo_obj:
                cargo_nome = cargo_obj.nome
        except Exception:
            pass
        finally:
            session_cargo.close()

        # Dispara a sequência em background: boas-vindas → 20s → verificação
        t = threading.Thread(
            target=_enviar_sequencia_emails,
            args=(name.strip(), whatsapp.strip(), email, codigo, cargo_nome),
            daemon=True,
        )
        t.start()

        # Notifica administradores via automação (se ativa)
        try:
            from views.automacao import notificar_novo_usuario
            from notification import Notificador as _Notificador
            notificar_novo_usuario(name.strip(), email, cargo_nome, _Notificador)
        except Exception:
            pass

        st.session_state.temp_email = email
        st.session_state.verificacao_pos_login = False
        st.success(
            'Cadastro realizado! Enviamos um e-mail de boas-vindas. '
            'O código de verificação será enviado em instantes.'
        )
        return True

    except OperationalError:
        session.rollback()
        st.error(
            'Banco de dados sem permissão de escrita. Verifique DATABASE_URL e as permissões do SQLite.')
        return False
    except Exception as e:
        session.rollback()
        st.error(f'Erro ao cadastrar: {e}')
        return False
    finally:
        session.close()


# =========================
# Verificação
# =========================
def verificar_codigo(email, codigo):
    session = Session()
    try:
        email = normalize_email(email)
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
                st.session_state.image = user_fresh.profile_image_path if user_fresh else None
                st.rerun()
            finally:
                session2.close()

            return True

        st.error('Código incorreto.')
        return False
    finally:
        session.close()


# =========================
# Login
# =========================
def autenticar_usuario(email, password):
    session = Session()
    try:
        email = normalize_email(email)
        user = session.query(UserAnalise).filter_by(email=email).first()

        if user:
            if not user.is_verified:
                st.warning(
                    'Sua conta ainda não foi verificada. '
                    'Por favor, insira o código de verificação enviado para seu e-mail.'
                )
                st.session_state.temp_email = user.email
                st.session_state.verificacao_pos_login = True
                return None

            if user.password and bcrypt.checkpw(password.encode(), user.password.encode()):
                return user

        st.error('Credenciais inválidas ou conta não verificada.')
        return None
    finally:
        session.close()


# =========================
# Recuperação de senha
# =========================
APP_BASE_URL = get_setting('APP_BASE_URL', 'http://localhost:8501')


def _build_reset_link(token: str) -> str:
    base = APP_BASE_URL
    if not base or str(base).strip().lower() in ('', 'none', 'null'):
        base = 'http://localhost:8501'
    base = str(base).rstrip('/')
    return f'{base}/?reset_token={token}'


def _enviar_email_recuperacao_bg(nome: str, email: str, link: str):
    try:
        Notificador().enviar_recuperacao_senha(nome, email, link)
        LOGGER.info('E-mail de recuperação enviado para %s', email)
    except Exception as exc:
        LOGGER.error('Falha no e-mail de recuperação para %s: %s', email, exc)


def _enviar_email_senha_alterada_bg(nome: str, email: str):
    try:
        Notificador().enviar_senha_alterada(nome, email)
        LOGGER.info('E-mail de confirmação de senha enviado para %s', email)
    except Exception as exc:
        LOGGER.error(
            'Falha no e-mail de confirmação de senha para %s: %s', email, exc)


def solicitar_recuperacao(email: str) -> bool:
    """Verifica e-mail no banco e dispara e-mail com link de recuperação."""
    email = normalize_email(email)
    if not email:
        st.error('Informe um e-mail válido.')
        return False

    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        if not user:
            st.error('E-mail não encontrado em nossa base de dados.')
            return False

        token = criar_token_para(session, PasswordReset, email)
        link = _build_reset_link(token)

        threading.Thread(
            target=_enviar_email_recuperacao_bg,
            args=(user.name, email, link),
            daemon=True,
        ).start()
        return True
    except Exception as e:
        session.rollback()
        st.error(f'Erro ao processar solicitação: {e}')
        return False
    finally:
        session.close()


def redefinir_senha(token: str, nova_senha: str) -> tuple[bool, str | None]:
    """Valida token, atualiza senha e retorna (ok, email_do_usuario)."""
    session = Session()
    try:
        reg = validar_token(session, PasswordReset, token)
        if not reg:
            return False, None

        email = reg.email
        if not atualizar_senha(session, UserAnalise, email, nova_senha):
            return False, None

        consumir_token(session, PasswordReset, token)

        user = session.query(UserAnalise).filter_by(email=email).first()
        if user:
            threading.Thread(
                target=_enviar_email_senha_alterada_bg,
                args=(user.name, email),
                daemon=True,
            ).start()
        return True, email
    except Exception as e:
        session.rollback()
        LOGGER.exception('Erro ao redefinir senha: %s', e)
        return False, None
    finally:
        session.close()


# =========================
# Diálogos explicativos do fluxo de recuperação
# =========================
@st.dialog('🔑 Recuperação de Senha')
def _dialog_iniciar_recuperacao():
    st.markdown(
        'Você será direcionado para a página de **Recuperar Minha Senha**.\n\n'
        'Informe o **e-mail cadastrado** em sua conta. Faremos uma verificação '
        'em nosso banco de dados e enviaremos um **link seguro** para você '
        'criar uma nova senha.\n\n'
        '⏱️ O link tem validade de **60 minutos** e só pode ser utilizado uma vez.'
    )
    if st.button('Continuar', use_container_width=True, key='dlg_rec_continuar'):
        st.session_state.pop('mostrar_dialog_iniciar_recuperacao', None)
        st.session_state.tela_auth = 'recuperar'
        st.rerun()


@st.dialog('📧 E-mail de Recuperação Enviado')
def _dialog_email_enviado():
    email = st.session_state.get('reset_email_destino', '')
    st.success('Verificamos seu e-mail com sucesso!')
    st.markdown(
        f'Enviamos um **link de recuperação** para:\n\n'
        f'**{email}**\n\n'
        '➡️ Acesse seu e-mail e clique no botão **"Redefinir Minha Senha"**.\n\n'
        '📂 Caso não encontre, verifique também a pasta de **spam** ou '
        '**lixo eletrônico**.'
    )
    if st.button('Entendi', use_container_width=True, key='dlg_email_ok'):
        st.session_state.pop('mostrar_dialog_email_enviado', None)
        st.rerun()


@st.dialog('🔐 Link Validado')
def _dialog_link_validado():
    st.success('Link de recuperação validado com sucesso!')
    st.markdown(
        'Agora crie uma **nova senha** para sua conta. Recomendações:\n\n'
        '- Use **ao menos 8 caracteres**.\n'
        '- Misture letras maiúsculas, minúsculas, números e símbolos.\n'
        '- **Não reutilize** senhas antigas.\n\n'
        'Você precisará digitar a senha **duas vezes** para confirmar.'
    )
    if st.button('Continuar', use_container_width=True, key='dlg_link_ok'):
        st.session_state.pop('mostrar_dialog_link_validado', None)
        st.rerun()


@st.dialog('✅ Senha Alterada com Sucesso')
def _dialog_senha_alterada():
    st.success('Sua nova senha foi cadastrada com sucesso!')
    st.markdown(
        'Um **e-mail de confirmação** foi enviado para sua conta.\n\n'
        'Você será **redirecionado automaticamente** para o '
        '**Oráculo Analista** ao clicar abaixo.'
    )
    if st.button('Acessar o Oráculo Analista', use_container_width=True, key='dlg_senha_ok'):
        st.session_state.pop('mostrar_dialog_senha_alterada', None)
        st.rerun()


def render_pagina_recuperar_senha():
    st.markdown('## 🔑 Recuperar Minha Senha')
    st.markdown(
        'Informe o **e-mail cadastrado** em sua conta. Vamos validar e enviar '
        'um link de redefinição de senha para você.'
    )

    with st.form('form_recuperar_senha'):
        email = st.text_input('E-mail cadastrado', key='rec_email_input')
        col1, col2 = st.columns(2)
        with col1:
            enviar = st.form_submit_button(
                '📧 Enviar Link de Recuperação', use_container_width=True)
        with col2:
            voltar = st.form_submit_button(
                '↩️ Voltar para Login', use_container_width=True)

    if voltar:
        st.session_state.tela_auth = 'login'
        st.rerun()

    if enviar:
        if solicitar_recuperacao(email):
            st.session_state.reset_email_destino = normalize_email(email)
            st.session_state.tela_auth = 'login'
            st.session_state.mostrar_dialog_email_enviado = True
            st.rerun()

    if st.session_state.get('mostrar_dialog_email_enviado'):
        _dialog_email_enviado()


def render_pagina_nova_senha(token: str):
    st.markdown('## 🔐 Criar Nova Senha')

    session = Session()
    try:
        reg = validar_token(session, PasswordReset, token)
    finally:
        session.close()

    if not reg:
        st.error(
            'Link inválido ou expirado. Solicite uma nova recuperação de senha.')
        if st.button('Voltar para Login'):
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.session_state.tela_auth = 'login'
            st.rerun()
        return

    # Diálogo de boas-vindas ao chegar pelo link (uma vez por token)
    flag_key = f'dialog_link_visto_{token[:12]}'
    if not st.session_state.get(flag_key):
        st.session_state.mostrar_dialog_link_validado = True
        st.session_state[flag_key] = True

    if st.session_state.get('mostrar_dialog_link_validado'):
        _dialog_link_validado()

    st.info(f'Redefinindo senha para: **{reg.email}**')

    with st.form('form_nova_senha'):
        nova = st.text_input('Nova senha', type='password', key='nova_senha_1')
        confirmar = st.text_input(
            'Confirmar nova senha', type='password', key='nova_senha_2')
        salvar = st.form_submit_button(
            '💾 Salvar Nova Senha', use_container_width=True)

    if salvar:
        if not nova or not confirmar:
            st.error('Preencha os dois campos de senha.')
            return
        if len(nova) < 8:
            st.error('A senha deve ter pelo menos 8 caracteres.')
            return
        if nova != confirmar:
            st.error('As senhas não coincidem.')
            return

        ok, email = redefinir_senha(token, nova)
        if not ok:
            st.error(
                'Não foi possível redefinir a senha. O link pode ter expirado.')
            return

        # Login automático
        session2 = Session()
        try:
            user = session2.query(UserAnalise).filter_by(email=email).first()
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.session_state.image = user.profile_image_path
                st.session_state.codigo_confirmado = True
        finally:
            session2.close()

        try:
            st.query_params.clear()
        except Exception:
            pass
        st.session_state.tela_auth = 'login'
        st.session_state.mostrar_dialog_senha_alterada = True
        st.rerun()


# =========================
# Interface de autenticação
# =========================
def interface():
    if st.session_state.get('logged_in'):
        return

    st.sidebar.title('Oráculo Analista')
    opcao = st.sidebar.radio('Selecione:', ['Login', 'Cadastrar'])

    if opcao == 'Cadastrar':
        nome = st.sidebar.text_input('Nome')
        zap = st.sidebar.text_input('WhatsApp')
        email = st.sidebar.text_input('Email')
        senha = st.sidebar.text_input('Senha', type='password')
        imagem = st.sidebar.file_uploader(
            'Imagem de Perfil', type=['png', 'jpg', 'jpeg'])

        if imagem:
            st.sidebar.image(imagem, caption='Pré-visualização', width=150)

        # Cargo fixo como Cliente (ID 3)
        cargo_id = None
        session = Session()
        try:
            cargo_obj = session.query(Cargo).filter(
                Cargo.nome.ilike('cliente')).first()
            if cargo_obj:
                cargo_id = cargo_obj.id
        except Exception:
            pass
        finally:
            session.close()

        if st.sidebar.button('Cadastrar'):
            erro = False
            if not nome:
                st.sidebar.error('Preencha o campo Nome.')
                erro = True
            if not zap:
                st.sidebar.error('Preencha o campo WhatsApp.')
                erro = True
            if not email:
                st.sidebar.error('Preencha o campo Email.')
                erro = True
            if not senha:
                st.sidebar.error('Preencha o campo Senha.')
                erro = True
            if not imagem:
                st.sidebar.error('Selecione uma Imagem de Perfil.')
                erro = True
            if cargo_id is None:
                st.sidebar.error('Cargo "Cliente" não encontrado no banco.')
                erro = True
            if not erro:
                cadastrar_usuario(nome, zap, email, senha, imagem, cargo_id)

    elif opcao == 'Login':
        email = st.sidebar.text_input('Email')
        senha = st.sidebar.text_input('Senha', type='password')

        if st.sidebar.button('Entrar'):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.session_state.image = user.profile_image_path
                st.rerun()

    st.sidebar.markdown('---')
    if st.sidebar.button('🔑 ESQUECI MINHA SENHA', use_container_width=True):
        st.session_state.mostrar_dialog_iniciar_recuperacao = True
        st.rerun()

    if st.session_state.get('mostrar_dialog_iniciar_recuperacao'):
        _dialog_iniciar_recuperacao()

    if 'temp_email' in st.session_state and not st.session_state.get('codigo_confirmado'):
        with st.sidebar:
            if st.session_state.get('verificacao_pos_login'):
                st.warning(
                    'Sua conta ainda não foi verificada. '
                    'Por favor, insira o código de verificação enviado para seu e-mail.'
                )
                codigo = st.text_input(
                    'Código de Verificação', key='codigo_login')
                if st.button('Confirmar Código', key='confirmar_codigo_login'):
                    verificar_codigo(st.session_state.temp_email, codigo)
            else:
                st.info(
                    f'Digite o código de verificação enviado para {st.session_state.temp_email}.')
                if st.button('Reenviar Código'):
                    session = Session()
                    try:
                        user = session.query(UserAnalise).filter_by(
                            email=normalize_email(st.session_state.temp_email)
                        ).first()
                        if user:
                            user.verification_code = gerar_codigo_verificacao()
                            session.commit()
                            try:
                                notificador = Notificador()
                                notificador.enviar_verificacao(
                                    user.name, user.email, user.verification_code)
                                st.success(
                                    'Código reenviado com sucesso! Verifique seu e-mail.')
                            except Exception:
                                st.error(
                                    'Não foi possível reenviar o e-mail de verificação agora.')
                    finally:
                        session.close()

                codigo = st.text_input(
                    'Código de Verificação', key='codigo_cadastro')
                if st.button('Confirmar Código', key='confirmar_codigo_cadastro'):
                    verificar_codigo(st.session_state.temp_email, codigo)

    if 'verificar_pagamento' not in st.session_state:
        st.session_state.verificar_pagamento = False

    if st.session_state.verificar_pagamento:
        st.markdown('### 🔒 Verificação de Pagamento do Plano')
        email_verificacao = st.text_input(
            'Digite seu e-mail de cadastro:', key='email_verif')

        if st.button('Verificar Status de Pagamento'):
            try:
                response = requests.get(
                    'http://localhost:8000/verificar-pagamento',
                    params={'email': email_verificacao},
                    timeout=20,
                )

                if response.status_code == 200:
                    dados = response.json()
                    if dados['status'] == 'confirmado':
                        st.success(
                            '✅ Pagamento confirmado! Código de verificação:')
                        st.code(dados['codigo_verificacao'])
                    else:
                        st.warning(dados['mensagem'])
                else:
                    st.error('❌ Não foi possível verificar o pagamento.')
            except Exception as e:
                st.error(f'Erro ao conectar com a API: {e}')


# =========================
# Landing / principal
# =========================
def main():
    # Roteamento por link de recuperação no e-mail (?reset_token=...)
    try:
        token_url = st.query_params.get('reset_token')
    except Exception:
        token_url = None

    if token_url and not st.session_state.get('logged_in'):
        render_pagina_nova_senha(token_url)
        if st.session_state.get('mostrar_dialog_senha_alterada'):
            _dialog_senha_alterada()
        return

    if st.session_state.get('mostrar_dialog_senha_alterada'):
        _dialog_senha_alterada()

    if not st.session_state.get('logged_in'):
        # Tela de "Recuperar Minha Senha"
        if st.session_state.get('tela_auth') == 'recuperar':
            st.sidebar.title('Oráculo Analista')
            st.sidebar.info('Modo: Recuperação de Senha')
            if st.sidebar.button('↩️ Voltar para Login', use_container_width=True):
                st.session_state.tela_auth = 'login'
                st.rerun()
            render_pagina_recuperar_senha()
            return

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

        if os.path.exists('./src/img/oraculo-analista.jpg'):
            st.image('./src/img/oraculo-analista.jpg', width=700)

        st.markdown('---')

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

        st.markdown('---')

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

        st.markdown('---')

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

        st.markdown('---')
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

        st.markdown('---')
        st.markdown(
            '<small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>',
            unsafe_allow_html=True,
        )

    else:
        user = st.session_state.user

        # Resolve nome do cargo
        session_cargo = Session()
        try:
            cargo_obj = session_cargo.query(Cargo).filter_by(id=user.cargo_id).first()
            cargo_nome = cargo_obj.nome if cargo_obj else ''
        finally:
            session_cargo.close()

        # Registra sessão ativa para monitoramento online
        try:
            from views.usuarios_online import registrar_sessao_ativa
            registrar_sessao_ativa(user.id, user.name, user.email)
        except Exception:
            pass

        # --- Sidebar: perfil ---
        st.sidebar.subheader(f'Bem-vindo(a), {user.name}')

        if user.profile_image_path and os.path.exists(user.profile_image_path):
            st.sidebar.image(user.profile_image_path, width=100)
        elif os.path.exists('./src/img/usuario.jpg'):
            st.sidebar.image('./src/img/usuario.jpg', width=100)

        st.sidebar.write(f'Email: {user.email}')
        st.sidebar.write(f'Cargo: {cargo_nome}')

        # --- Determina páginas permitidas ---
        from views.permissoes import obter_paginas_por_cargo
        paginas_disponiveis = obter_paginas_por_cargo(cargo_nome)

        # Ícones de navegação
        _icones = {
            'Oráculo Analista': '🤖',
            'Dashboard': '📊',
            'Clientes': '👥',
            'Parceiros': '🤝',
            'Financeiro': '💰',
            'Configuração': '⚙️',
            'Usuários Online': '🟢',
            'Automação': '🤖',
            'Banco de Dados': '🗄️',
        }
        opcoes_menu = [f"{_icones.get(p, '')} {p}" for p in paginas_disponiveis]

        st.sidebar.markdown('---')
        st.sidebar.markdown('### 📋 Menu')
        selecao = st.sidebar.radio(
            'Navegação',
            opcoes_menu,
            label_visibility='collapsed',
            key='menu_nav',
        )
        # Extrai nome da página sem ícone
        pagina_atual = selecao.split(' ', 1)[-1].strip()

        st.sidebar.markdown('---')
        if st.sidebar.button('🔓 Sair do sistema'):
            for key in [
                'user', 'logged_in', 'codigo_confirmado', 'temp_email',
                'name', 'email', 'image', 'primeiro_nome', 'messages',
                'full_content', 'menu_nav',
            ]:
                st.session_state.pop(key, None)
            st.rerun()

        # --- Renderiza página selecionada ---
        if pagina_atual == 'Oráculo Analista':
            oraculo_analista()

        elif pagina_atual == 'Dashboard':
            from views.dashboard import render_dashboard
            render_dashboard(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Clientes':
            from views.clientes import render_clientes
            render_clientes(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Parceiros':
            from views.parceiros import render_parceiros
            render_parceiros(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Financeiro':
            from views.financeiro import render_financeiro
            render_financeiro(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Configuração':
            st.session_state.user_id = user.id
            from views.configuracao import render_configuracao
            render_configuracao(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Usuários Online':
            from views.usuarios_online import render_usuarios_online
            render_usuarios_online(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Automação':
            from views.automacao import render_automacao
            render_automacao(Session, UserAnalise, Cargo)

        elif pagina_atual == 'Banco de Dados':
            from views.banco_dados import render_banco_dados
            render_banco_dados(Session, UserAnalise, Cargo, DATABASE_URL)


if __name__ == '__main__':
    st.set_page_config(page_title='Oráculo Analista',
                       page_icon='📊', layout='wide')
    main()
