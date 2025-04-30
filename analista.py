import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import json
import xml.etree.ElementTree as ET
from docx import Document
import os
import base64
import re
import replicate
from decouple import config

# Verificar se o token está configurado
REPLICATE_API_TOKEN = 'r8_9qyeytR9OiIobAQ1f0TzU3TGKJBLSzI0ti8Jp'


# Funções de leitura de arquivos (mantidas iguais ao código anterior)
def read_xlsx(file):
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with pd.ExcelFile(file) as xls:
        with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                txt_file.write(f'--- Aba: {sheet_name} ---\n')
                df.to_csv(txt_file, sep='\t', index=False, header=True)
                txt_file.write('\n')
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        return arquivo.read()


def read_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    return text


def read_json(file):
    content = json.load(file)
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(json.dumps(content, indent=4))
    return json.dumps(content, indent=4)


def read_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(xml_str)
    return xml_str


def read_html(file):
    html_content = file.read().decode("utf-8")
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(html_content)
    return html_content


def read_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    return text


def read_txt(file):
    return file.read().decode("utf-8")


# Dicionário de ícones
icons = {
    "assistant": "./src/img/perfil-analista.png",  # Ícone padrão do assistente
    "user": "./src/img/usuario.jpg"  # Ícone padrão do usuário
}

default_avatar_path = "./src/img/usuario.jpg"


def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Função para carregar arquivos
def carregar_arquivos():
    uploaded_files = st.sidebar.file_uploader(
        "Coloque seu arquivo aqui:",
        type=["xlsx", "pdf", "xml", "json", "html", "htm", "doc", "docx", "txt", "xls"],
        accept_multiple_files=True
    )

    if st.sidebar.button('CARREGAR'):
        conteudos = []
        for file in uploaded_files:
            st.write(f"**Arquivo carregado:** {file.name}")
            if file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                conteudo = read_xlsx(file)
            elif file.type == "application/pdf":
                conteudo = read_pdf(file)
            elif file.type == "application/json":
                conteudo = read_json(file)
            elif file.type in ["application/xml", "text/xml"]:
                conteudo = read_xml(file)
            elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                conteudo = read_docx(file)
            elif file.type == "text/plain":
                conteudo = read_txt(file)
            elif file.type in ["text/html", "text/htm"]:
                conteudo = read_html(file)
            conteudos.append(conteudo)
        return conteudos
    return []


def obter_avatar_usuario(user_id):
    caminho_avatar = f"./src/img/usuarios/{user_id}.jpg"
    return caminho_avatar if os.path.exists(caminho_avatar) else icons["user"]



# Interface principal do Streamlit
def oraculo_analista():
    st.title("Chatbot Poderoso para Análise de Documentos")

    # Carregar arquivos
    conteudos = carregar_arquivos()

    if conteudos:
        st.subheader("Conteúdo dos Arquivos Carregados:")
        full_content = "\n".join(conteudos)
        st.session_state.full_content = full_content  # Armazena o conteúdo completo
        for i, conteudo in enumerate(conteudos):
            st.text_area(f"Conteúdo do Arquivo {i+1}", conteudo, height=200)

    # Sidebar com informações e botões
    with st.sidebar:
        st.markdown(
            """
            <h1 style='text-align: center;'>ORÁCULO ANALISTA</h1>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <style>
            .cover-glow {
                width: 100%;
                height: auto;
                padding: 3px;
                box-shadow: 
                    0 0 5px #002F6C,    /* Azul Profundo */
                    0 0 10px #C0C0C0,   /* Prata Metálico */
                    0 0 15px #D4AF37,   /* Ouro Suave */
                    0 0 20px #4A4A4A,   /* Cinza Escuro */
                    0 0 25px #FFFFFF,    /* Branco */
                    0 0 30px #002F6C,   /* Azul Profundo */
                    0 0 35px #C0C0C0;    /* Prata Metálico */
                position: relative;
                z-index: -1;
                border-radius: 30px;  /* Cantos arredondados */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Exibir imagem na sidebar com efeito de brilho
        img_path = "./src/img/oraculo-analista.jpg"
        img_base64 = img_to_base64(img_path)
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )

        # Botão para limpar histórico
        def clear_chat_history():
            st.session_state.messages = [{"role": "assistant", "content": '🌟 Bem-vindo ao Oráculo Analista! Estou aqui para te ajudar a analisar documentos. Carregue seus arquivos e faça suas perguntas! 💡'}]

        st.sidebar.markdown("---")
        st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history)

        st.sidebar.markdown("Desenvolvido por [WILLIAM EUSTÁQUIO](https://www.instagram.com/flashdigital.tech/)")

    # Inicializar estado da conversa
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{
            "role": "assistant",
            "content": '🌟 Bem-vindo ao Oráculo Analista! Estou aqui para te ajudar a analisar documentos. Carregue seus arquivos e faça suas perguntas! 💡'
        }]

    # Exibir mensagens anteriores com perfil do usuário
    for message in st.session_state.messages:
        user_id = message.get("user_id", "default")
        avatar_image = obter_avatar_usuario(user_id) if message["role"] == "user" else icons["assistant"]

        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua pergunta aqui:"):
        user_id = st.session_state.get("user_id", "default")
        avatar_image = obter_avatar_usuario(user_id)

        st.session_state.messages.append({"role": "user", "content": prompt, "user_id": user_id})
        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)

        # Geração da resposta
        with st.chat_message("assistant", avatar=icons["assistant"]):
            try:
                system_prompt = f"""
                Você é o Oráculo Analista, especializado em responder perguntas sobre documentos carregados.
                Conteúdo dos documentos carregados:
                {st.session_state.get('full_content', '')}
                """
                full_prompt = f"{system_prompt}\n\nPergunta do usuário: {prompt}"

                full_response = ""
                stream = replicate.stream(
                    "deepseek-ai/deepseek-r1",
                    input={"top_p": 1, "prompt": full_prompt, "max_tokens": 2048, "temperature": 0.1}
                )

                with st.spinner("Gerando análise..."):
                    response_container = st.empty()
                    for event in stream:
                        full_response += str(event)
                        clean_response = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
                        response_container.markdown(clean_response)

                st.session_state.messages.append({"role": "assistant", "content": clean_response})
            except Exception as e:
                st.error(f"Erro ao gerar análise: {str(e)}")

if __name__ == "__main__":
    oraculo_analista()