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
import io
from fpdf import FPDF



# 🔧 CONFIGURAÇÕES INICIAIS

REPLICATE_API_TOKEN = config('REPLICATE_API_TOKEN')
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

icons = {
    "assistant": "./src/img/perfil-analista.png",
    "user": "./src/img/usuario.jpg"
}


# 🧠 GERENCIAMENTO DE SESSÃO E USUÁRIO

def atualizar_primeiro_nome():
    if "user" in st.session_state:
        nome_completo = st.session_state.user.name.strip()
        primeiro_nome = nome_completo.split()[0]
        st.session_state["primeiro_nome"] = primeiro_nome

def atualizar_imagem_perfil(email):
    image_path = os.path.join(PROFILE_IMAGES_DIR, f"{email}.png")
    if os.path.exists(image_path):
        st.session_state.image = image_path

def configurar_usuario_logado(user):
    st.session_state.name = user.name
    st.session_state.email = user.email
    st.session_state.image = user.profile_image_path
    st.session_state.primeiro_nome = user.name.split(" ")[0]

def obter_avatar_usuario():
    user = st.session_state.get("user")
    if user and user.profile_image_path and os.path.exists(user.profile_image_path):
        return user.profile_image_path
    return "./src/img/usuario.jpg"


# 📄 LEITORES DE ARQUIVOS

def read_xlsx(file):
    text = ""
    with pd.ExcelFile(file) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            text += f'--- Aba: {sheet_name} ---\n{df.to_string()}\n\n'
    return text

def read_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_json(file):
    return json.dumps(json.load(file), indent=4)

def read_xml(file):
    tree = ET.parse(file)
    return ET.tostring(tree.getroot(), encoding='utf-8').decode('utf-8')

def read_html(file):
    return file.read().decode("utf-8")

def read_docx(file):
    doc = Document(file)
    return '\n'.join(paragraph.text for paragraph in doc.paragraphs)

def read_txt(file):
    return file.read().decode("utf-8")


# 📤 CARREGAMENTO DE ARQUIVOS PARA ANÁLISE

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
            else:
                conteudo = "Tipo de arquivo não suportado."

            conteudos.append(conteudo)

    return conteudos


# 💬 INTERFACE PRINCIPAL DO CHAT ANALISTA

def oraculo_analista():
    atualizar_primeiro_nome()

    st.markdown(
        """
        <style>
        .highlight-creme {
            background: linear-gradient(90deg, #f5f5dc, gold);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .highlight-dourado {
            background: linear-gradient(90deg, gold, #f5f5dc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"<h1 class='title'>Análise rápida e precisa com o <span class='highlight-creme'>Oráculo</span> " 
        f"<span class='highlight-dourado'>Analista</span></h1>",
        unsafe_allow_html=True
    )

    st.sidebar.image("./src/img/perfil-analista.png", width=500)

    if st.sidebar.button("🔄 Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

    conteudos = carregar_arquivos()

    if conteudos:
        st.subheader("Conteúdo dos Arquivos Carregados:")
        full_content = "\n".join(conteudos)
        st.session_state.full_content = full_content
        for i, conteudo in enumerate(conteudos):
            st.text_area(f"Conteúdo do Arquivo {i+1}", conteudo, height=200)

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f'🌟 {st.session_state.get("primeiro_nome", "Usuário")}, estou aqui para te ajudar a analisar documentos. Carregue seus arquivos e faça suas perguntas! 💡'
        }]

    for message in st.session_state.messages:
        avatar_image = obter_avatar_usuario() if message["role"] == "user" else icons["assistant"]
        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    if prompt := st.chat_input("Digite sua pergunta aqui:"):
        avatar_image = obter_avatar_usuario()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)

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
                    "anthropic/claude-3.7-sonnet",
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

        if st.session_state.get("messages"):
            chat_text = [
                {"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]
            ]
            df = pd.DataFrame(chat_text)

            # 📊 Excel com estilo
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Conversa', index=False)

                workbook = writer.book
                worksheet = writer.sheets['Conversa']
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 40)

            excel_buffer.seek(0)
            st.download_button(
                "📊 Baixar conversa em Excel",
                data=excel_buffer,
                file_name="chat_oraculo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 📄 PDF com estilo
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, "Oráculo Analista - Histórico de Conversa", ln=True, align="C")
            pdf.ln(5)
            pdf.set_font("Arial", size=12)

            def remover_emojis(texto):
                return re.sub(r'[^\x00-\x7F]+', '', texto)

            for m in chat_text:
                role = remover_emojis(m['role'].capitalize())
                content = remover_emojis(m['content'])
                pdf.multi_cell(0, 10, f"{role}: {content}", border=0)

            pdf_buffer = io.BytesIO()
            pdf.output(pdf_buffer, 'F')
            pdf_buffer.seek(0)

            st.download_button(
                "📄 Baixar conversa em PDF",
                data=pdf_buffer,
                file_name="chat_oraculo.pdf",
                mime="application/pdf"
            )


# PONTO DE ENTRADA

if __name__ == "__main__":
    oraculo_analista()
