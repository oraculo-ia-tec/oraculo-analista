import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
import requests
from PIL import Image
import io
import string
import random
from analista import oraculo_analista
import streamlit as st
from PIL import Image
from streamlit_extras.colored_header import colored_header
from decouple import config


DATABASE_URL = config("DATABASE_URL")
WEBHOOK_CADASTRO_ANALISTA = "https://hook.us2.make.com/rw8eir16jp5eohnndnjtosange86i1i5"

# Configuração do banco de dados
DATABASE_URL = config("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

PROFILE_IMAGES_DIR = "./user_profiles/"  # Diretório para salvar imagens de perfil

# Criar diretório para imagens de perfil, se não existir
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)


# Modelo de Usuário no Banco de Dados
class UserAnalise(Base):
    __tablename__ = "user_analise"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Nome com limite de 255 caracteres
    whatsapp = Column(String(20), nullable=False)  # Número de WhatsApp com limite de 20 caracteres
    email = Column(String(255), unique=True, nullable=False)  # E-mail com limite de 255 caracteres
    profile_image_path = Column(String(500), nullable=True)  # Caminho da imagem de perfil com limite de 500 caracteres
    verification_code = Column(String(6), nullable=True)  # Código de verificação com limite de 6 caracteres
    is_verified = Column(String(10), default="false")  # Status de verificação


# Criar tabelas no banco de dados
Base.metadata.create_all(engine)


# Carregar a imagem do robô
robot_image = Image.open("./src/img/oraculo-analista-home2.png")  # Caminho da imagem

# Estilos personalizados para títulos e subtítulos
st.markdown("""
    <style>
        /* Centralizar a imagem */
        .image-container {
            text-align: center;
        }

        /* Estilo para títulos principais (gradiente violeta com branco) */
        .title {
            font-size: 48px;
            font-weight: bold;
            color: white;
            text-align: center;
            background: linear-gradient(90deg, #8A2BE2, #FFFFFF);
            -webkit-background-clip: text;
            background-clip: text;
            margin-bottom: 20px;
        }
        /* Estilo para subtítulos (gradiente violeta com branco) */
        .subtitle {
            font-size: 24px;
            color: white;
            text-align: center;
            background: linear-gradient(90deg, #8A2BE2, #FFFFFF);
            -webkit-background-clip: text;
            background-clip: text;
            margin-bottom: 40px;
        }
        /* Estilo para cabeçalhos de seção (gradiente violeta com branco) */
        .section-header {
            font-size: 32px;
            font-weight: bold;
            color: white;
            text-align: left;
            background: linear-gradient(90deg, #8A2BE2, #FFFFFF);
            -webkit-background-clip: text;
            background-clip: text;
            margin-top: 40px;
            margin-bottom: 20px;
        }
        /* Estilo para itens de benefícios (fonte branca) */
        .benefit-item {
            font-size: 18px;
            color: white;
            margin-bottom: 10px;
        }
        /* Estilo para ícones */
        .icon {
            font-size: 24px;
            color: white;
            margin-right: 10px;
        }
        /* Estilo geral para o fundo da página */
        body {
            background-color: #121212; /* Fundo escuro para destacar o gradiente */
            color: white; /* Textos padrão em branco */
        }
    </style>
""", unsafe_allow_html=True)

# Título principal com imagem do robô
st.markdown('<p class="title">Oráculo Analista</p>', unsafe_allow_html=True)
st.image(robot_image, width=350)
st.markdown('<p class="subtitle">Sua ferramenta inteligente para análise de dados e tomada de decisões estratégicas</p>', unsafe_allow_html=True)

# Seção 1: Introdução ao Oráculo Analista
colored_header(label="Introdução ao Oráculo Analista", description="", color_name="blue-70")
st.write("""
O **Oráculo Analista** é uma ferramenta avançada que realiza a leitura e análise de documentos e bancos de dados de forma rápida e eficiente. 
Seu objetivo é facilitar a tomada de decisões para empresários, proporcionando respostas precisas e soluções estratégicas.
""")

# Seção 2: Vantagens do Oráculo Analista
colored_header(label="Vantagens do Oráculo Analista", description="", color_name="blue-70")
col1, col2 = st.columns(2)

with col1:
    st.markdown('<p class="section-header">Agilidade nas Respostas</p>', unsafe_allow_html=True)
    st.markdown("""
    - Processamento rápido de grandes volumes de dados em tempo real.
    - Respostas instantâneas a perguntas complexas sobre documentos.
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<p class="section-header">Precisão nas Análises</p>', unsafe_allow_html=True)
    st.markdown("""
    - Uso de inteligência artificial para interpretar dados e minimizar erros humanos.
    - Resultados consistentes e confiáveis para decisões informadas.
    """, unsafe_allow_html=True)

# Seção 3: Benefícios para Empresários
colored_header(label="Benefícios para Empresários", description="", color_name="blue-70")
benefits = [
    ("Aumento de Faturamento", "Identificação de oportunidades estratégicas e análise de mercado."),
    ("Redução de Custos", "Detecção de ineficiências operacionais e otimização de processos."),
    ("Previsibilidade e Segurança", "Projeções baseadas em dados históricos para planejamento estratégico.")
]

for title, description in benefits:
    st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="benefit-item">{description}</p>', unsafe_allow_html=True)

# Seção 4: Resultados Gerados pelo Oráculo Analista
colored_header(label="Resultados Gerados pelo Oráculo Analista", description="", color_name="blue-70")
results = [
    ("Decisões Baseadas em Dados", "Adoção de uma abordagem orientada por dados para decisões mais eficazes."),
    ("Eficiência Operacional", "Melhoria nos processos de negócios e redução de tarefas administrativas."),
    ("Crescimento Sustentável", "Foco em estratégias de longo prazo para crescimento saudável.")
]

for title, description in results:
    st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="benefit-item">{description}</p>', unsafe_allow_html=True)

# Seção 5: Conclusão
colored_header(label="Conclusão", description="", color_name="blue-70")
st.write("""
O **Oráculo Analista** é uma solução poderosa que transforma a maneira como os empresários interagem com informações complexas e grandes volumes de dados. 
Com suas vantagens e benefícios, ele não só facilita a tomada de decisões, mas também garante resultados significativos em eficiência e crescimento, tornando-se um aliado indispensável para qualquer empresário que busque inovação e agilidade nos negócios.
""")

# Botão de Chamada à Ação
st.markdown('<div style="text-align: center; margin-top: 40px;">', unsafe_allow_html=True)
if st.button("Comece Agora ➡️", use_container_width=True):
    st.write("Redirecionando para o cadastro...")
    # Aqui você pode adicionar a lógica para redirecionar o usuário para a página de cadastro
st.markdown('</div>', unsafe_allow_html=True)



# Função para salvar a imagem de perfil
def save_profile_image(image, user_email):
    try:
        image_path = os.path.join(PROFILE_IMAGES_DIR, f"{user_email}.png")
        with open(image_path, "wb") as f:
            f.write(image.getbuffer())
        return image_path
    except Exception as e:
        st.error(f"Erro ao salvar a imagem de perfil: {str(e)}")
        return None


# Função para gerar código de verificação
def gerar_codigo_verificacao(tamanho=6):
    caracteres = string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))


# Função para enviar dados ao Webhook do Make
def send_to_make_webhook(data):
    if not WEBHOOK_CADASTRO_ANALISTA:
        st.error("A URL do Webhook não está configurada. Verifique o arquivo .env.")
        return False

    try:
        response = requests.post(WEBHOOK_CADASTRO_ANALISTA, json=data)
        if response.status_code == 200:
            st.success("Dados enviados ao Make com sucesso!")
            return True
        else:
            st.warning(f"Erro ao enviar dados ao Make. Status code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Erro ao enviar dados ao Make: {str(e)}")
        return False


# Função para exibir a janela de diálogo
@st.dialog("Cadastro Concluído")
def show_success_dialog():
    st.write("🎉 **Cadastro realizado com sucesso!**")
    st.write("Por favor, verifique seu e-mail para obter o código de verificação.")
    st.write("Você precisará desse código para acessar o Oráculo Analista.")

    if st.button("Fechar"):
        st.session_state.show_dialog = False
        st.rerun()


# Função para registrar um novo usuário
def register_user_analise(name, whatsapp, email, profile_image):
    st.session_state.show_dialog = True

    session = Session()
    try:
        # Verificar se o e-mail já está cadastrado
        existing_user = session.query(UserAnalise).filter_by(email=email).first()
        if existing_user:
            st.error("E-mail já cadastrado. Por favor, use outro e-mail.")
            return False

        # Gerar código de verificação
        codigo = gerar_codigo_verificacao()

        # Salvar a imagem de perfil
        profile_image_path = save_profile_image(profile_image, email)
        if not profile_image_path:
            return False

        # Criar novo usuário
        new_user = UserAnalise(
            name=name,
            whatsapp=whatsapp,
            email=email,
            profile_image_path=profile_image_path,
            verification_code=codigo,
            is_verified="false"
        )
        session.add(new_user)
        session.commit()

        # Preparar dados para o Webhook
        user_data = {
            "name": name,
            "whatsapp": whatsapp,
            "email": email,
            "profile_image_path": profile_image_path,
            "verification_code": codigo
        }

        # Enviar dados ao Webhook do Make
        send_to_make_webhook(user_data)
    except Exception as e:
        st.error(f"Erro ao cadastrar usuário: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


# Função para verificar código de verificação
def verify_user(email, codigo):
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        if not user:
            st.error("Usuário não encontrado.")
            return False
        if user.verification_code == codigo:
            user.is_verified = "true"
            session.commit()
            st.success("Cadastro confirmado com sucesso!")
            return True
        else:
            st.error("Código de verificação inválido.")
            return False
    except Exception as e:
        st.error(f"Erro ao verificar código: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


# Interface de Login/Cadastro
def login_or_register():
    st.sidebar.title("Oráculo Analista - Login/Cadastro")

    # Opção de login ou cadastro
    option = st.sidebar.selectbox("Escolha uma opção:", ["Login", "Cadastrar"])

    if option == "Cadastrar":
        st.sidebar.subheader("Cadastro de Usuário")
        name = st.sidebar.text_input("Nome Completo")
        whatsapp = st.sidebar.text_input("WhatsApp")
        email = st.sidebar.text_input("E-mail")
        profile_image = st.sidebar.file_uploader("Carregar Imagem de Perfil", type=["png", "jpg", "jpeg"])

        if st.sidebar.button("Cadastrar"):
            if not name or not whatsapp or not email or not profile_image:
                st.sidebar.error("Preencha todos os campos.")
            else:
                if register_user_analise(name, whatsapp, email, profile_image):
                    st.sidebar.success("Verifique seu e-mail para confirmar o cadastro.")

    elif option == "Login":
        st.sidebar.subheader("Login de Usuário")
        email = st.sidebar.text_input("E-mail")
        codigo = st.sidebar.text_input("Código de Verificação", type="password")

        if st.sidebar.button("Entrar"):
            if verify_user(email, codigo):
                user = authenticate_user(email)
                if user:
                    st.session_state.user = user
                    st.sidebar.success(f"Bem-vindo, {user.name}!")


# Função para autenticar o usuário
def authenticate_user(email):
    session = Session()
    try:
        user = session.query(UserAnalise).filter_by(email=email).first()
        if user and user.is_verified == "true":
            return user
        return None
    except Exception as e:
        st.error(f"Erro ao autenticar usuário: {str(e)}")
        return None
    finally:
        session.close()


# Função principal do aplicativo
def main():
    # Verifica se o usuário está logado
    if "user" not in st.session_state:
        login_or_register()
    else:
        # Exibir informações do perfil do usuário
        user = st.session_state.user
        st.sidebar.subheader("Perfil do Usuário")
        st.sidebar.image(user.profile_image_path, caption=f"Olá, {user.name}", width=100)
        st.sidebar.write(f"WhatsApp: {user.whatsapp}")
        st.sidebar.write(f"E-mail: {user.email}")

        # Chamar a função do Oráculo Analista
        oraculo_analista()


if __name__ == "__main__":
    main()