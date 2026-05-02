import streamlit as st
from PIL import Image
from streamlit_extras.colored_header import colored_header

# Carregar a imagem do robô
robot_image = Image.open("./src/img/oraculo-analista-home2.png")  # Caminho da imagem

# Configuração da página
st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados para títulos e subtítulos
st.markdown("""
    <style>
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
st.image(robot_image, width=200, caption="Oráculo Analista")
st.markdown('<p class="title">Oráculo Analista</p>', unsafe_allow_html=True)
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
if st.button("Comece Agora ➡️", width='stretch'):
    st.write("Redirecionando para o cadastro...")
    # Aqui você pode adicionar a lógica para redirecionar o usuário para a página de cadastro
st.markdown('</div>', unsafe_allow_html=True)