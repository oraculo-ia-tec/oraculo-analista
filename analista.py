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


# Diretório das imagens de perfil
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)


# Dicionário de ícones
icons = {
    "assistant": "./src/img/perfil-analista.png",
    "user": "./src/img/usuario.jpg"
}

def obter_avatar_usuario():
    if "image" in st.session_state:
        return st.session_state.image
    else:
        return icons["user"]

# Carregar arquivos (função permanece igual ao original)
def carregar_arquivos():
    uploaded_files = st.sidebar.file_uploader(
        "Coloque seu arquivo aqui:",
        type=["xlsx", "pdf", "xml", "json", "html", "htm", "doc", "docx", "txt", "xls"],
        accept_multiple_files=True
    )

    conteudos = []
    if st.sidebar.button('CARREGAR'):
        for file in uploaded_files:
            st.write(f"**Arquivo carregado:** {file.name}")
            # Lógica para leitura dos arquivos, conforme tipo
            # Utilize o código original aqui

    return conteudos

# Interface principal
def oraculo_analista():
    st.title("Chatbot Poderoso para Análise de Documentos")

    conteudos = carregar_arquivos()

    if conteudos:
        st.subheader("Conteúdo dos Arquivos Carregados:")
        full_content = "\n".join(conteudos)
        st.session_state.full_content = full_content
        for i, conteudo in enumerate(conteudos):
            st.text_area(f"Conteúdo do Arquivo {i+1}", conteudo, height=200)

    # Inicializar estado da conversa
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{
            "role": "assistant",
            "content": '🌟 Bem-vindo ao Oráculo Analista! Estou aqui para te ajudar a analisar documentos. Carregue seus arquivos e faça suas perguntas! 💡'
        }]

    # Exibir mensagens anteriores com perfil do usuário
    for message in st.session_state.messages:
        avatar_image = obter_avatar_usuario() if message["role"] == "user" else icons["assistant"]

        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua pergunta aqui:"):
        avatar_image = obter_avatar_usuario()

        st.session_state.messages.append({"role": "user", "content": prompt})
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