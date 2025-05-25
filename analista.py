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

            if file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             "application/vnd.ms-excel"]:
                conteudo = read_xlsx(file)
            elif file.type == "application/pdf":
                conteudo = read_pdf(file)
            elif file.type == "application/json":
                conteudo = read_json(file)
            elif file.type in ["application/xml", "text/xml"]:
                conteudo = read_xml(file)
            elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               "application/msword"]:
                conteudo = read_docx(file)
            elif file.type == "text/plain":
                conteudo = read_txt(file)
            elif file.type in ["text/html", "text/htm"]:
                conteudo = read_html(file)
            else:
                conteudo = "Tipo de arquivo não suportado."

            conteudos.append(conteudo)

    return conteudos


# 🔍 DETECÇÃO DE INTENÇÃO

def verificar_intencao_usuario(prompt):
    prompt = prompt.lower()
    if any(p in prompt for p in ["plano", "assinar", "upgrade", "mensal", "trimestral", "anual", "contratar", "preço"]):
        return "plano"
    if any(p in prompt for p in ["reunião", "agendar", "consultoria", "falar com o desenvolvedor", "encontro"]):
        return "reuniao"
    return None


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
            st.text_area(f"Conteúdo do Arquivo {i + 1}", conteudo, height=200)

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f'🌟 {st.session_state.get("primeiro_nome", "Usuário")}, estou aqui para te ajudar a analisar documentos. Carregue seus arquivos e faça suas perguntas! 💡'
        }]

    for message in st.session_state.messages:
        avatar_image = obter_avatar_usuario() if message["role"] == "user" else icons["assistant"]
        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    if prompt := st.chat_input("Digite sua pergunta aqui:", key="chat_input_analista"):
        avatar_image = obter_avatar_usuario()

        intencao = verificar_intencao_usuario(prompt)
        if intencao == "plano":
            with st.chat_message("assistant", avatar=icons["assistant"]):
                st.markdown("💡 Percebi que você está interessado em nossos planos! Veja as opções abaixo:")
                # Popover para escolher o plano
                with st.popover("ESCOLHA SEU PLANO"):
                    st.markdown("### 💼 Planos Oráculo Analista")
                    st.write("Escolha um dos planos abaixo para liberar recursos avançados.")

                    # Criando duas colunas
                    col1, col2 = st.columns(2)

                    with col1:
                        # Apresentar os planos
                        plano = st.radio("Selecione um plano:",
                                         ["Mensal - R$ 49,90", "Trimestral - R$ 119,90", "Anual - R$ 369,90"])

                    with col2:
                        # Breve descrição de cada plano
                        if plano == "Mensal - R$ 49,90":
                            st.write("Ideal para quem deseja experimentar nossos serviços por um curto período.")
                        elif plano == "Trimestral - R$ 119,90":
                            st.write("Economize em relação ao plano mensal e tenha mais tempo para aproveitar.")
                        elif plano == "Anual - R$ 369,90":
                            st.write(
                                "A melhor opção para quem deseja um compromisso a longo prazo com descontos significativos.")

                    if st.button("Assinar agora"):
                        if plano == "Mensal - R$ 49,90":
                            st.write("Você será redirecionado para o link de simulação do plano mensal.")
                            st.markdown(
                                "[Clique aqui para assinatura mensal](https://sandbox.asaas.com/c/qmo94xid8f1i6tnc)")
                        elif plano == "Trimestral - R$ 119,90":
                            st.write("Você será redirecionado para o link de simulação do plano trimestral.")
                            st.markdown(
                                "[Clique aqui para assinatura trimestral](https://sandbox.asaas.com/c/jsmak76vdo5fke23)")
                        elif plano == "Anual - R$ 369,90":
                            st.write("Você será redirecionado para o link de simulação do plano anual.")
                            st.markdown(
                                "[Clique aqui para assinatura anual](https://sandbox.asaas.com/c/adu6nd24lf8jauo3)")
        elif intencao == "reuniao":

            with st.chat_message("assistant", avatar=icons["assistant"]):
                st.markdown("📅 Parece que você deseja agendar uma reunião! Preencha as informações abaixo:")
                st.markdown(
                    "Assim que você finalizar o cadastro de agendamento você receberá uma confirmação em seu e-mail.")
                with st.popover("Agendamento"):
                    st.markdown("### 📅 Agende uma reunião com o Oráculo Analista")
                    nome = st.text_input("Nome completo")
                    empresa = st.text_input("Empresa (opcional)")
                    whatsapp = st.text_input("WhatsApp")
                    email = st.text_input("E-mail")
                    data = st.date_input("Data")
                    hora = st.time_input("Horário")

                    if st.button("Cadastrar"):
                        st.write("Nome:", nome)
                        st.write("Empresa:", empresa)
                        st.write("WhatsApp:", whatsapp)
                        st.write("E-mail:", email)
                        st.write("Data:", data)
                        st.write("Horário:", hora)
                if st.button("Confirmar Agendamento"):
                    import requests
                    from decouple import config

                    WEBHOOK_AGENDA_ANALISTA = config('WEBHOOK_AGENDA_ANALISTA')

                    dados_agenda = {
                        "nome": nome,
                        "empresa": empresa,
                        "whatsapp": whatsapp,
                        "email": email,
                        "data": str(data),
                        "hora": str(hora)
                    }

                    try:
                        resposta = requests.post(WEBHOOK_AGENDA_ANALISTA, json=dados_agenda)
                        if resposta.status_code == 200:
                            st.success("✅ Pedido de agendamento feito com sucesso!")
                            st.balloons
                            st.info('Enviei um confirmaçao de agendamento e seu e-mail.')
                        else:
                            st.error("❌ Erro ao enviar agendamento para o Oráculo Analista.")
                    except Exception as e:
                        st.error(f"Erro ao enviar para Webhook: {e}")

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)

        with st.chat_message("assistant", avatar=icons["assistant"]):
            try:
                system_prompt = f"""
                    Você é o Oráculo Analista, doutor e especializado especialisra em análise de dados. 
                    Sua missão é dá respostas precisas e exatas sobre documentos carregados, com no máximo 256 
                    caracteres por resposta — ou até 300 caracteres se necessário para completude.             
                    Conteúdo dos documentos carregados:
                    {st.session_state.get('full_content', '')}.

                    Fornecer informações precisas:
                        "Análise do arquivo {st.session_state.get('full_content', '')}: forneça uma visão geral do conteúdo e estrutura do arquivo."
                        "Leia o arquivo {st.session_state.get('full_content', '')} e extraia as principais informações sobre [tópico_específico]."
                        "Faça uma análise detalhada do arquivo {st.session_state.get('full_content', '')} e forneça uma lista de pontos-chave."
                        Fornecer previsões sobre eventos futuros
                        "Com base na análise do arquivo {st.session_state.get('full_content', '')}, preveja as tendências futuras para [tópico_específico]."
                        "Leia o arquivo {st.session_state.get('full_content', '')} e forneça uma previsão sobre o impacto de [evento_ou_decisão] nos próximos [período_de_tempo]."
                        "Faça uma análise de risco do arquivo {st.session_state.get('full_content', '')} e forneça uma previsão sobre a probabilidade de [evento_ou_resultado]."
                        Fornecer recomendações ou decisões baseadas em regras e lógica
                        "Com base na análise do arquivo {st.session_state.get('full_content', '')}, forneça recomendações para [problema_ou_decisão]."
                        "Leia o arquivo {st.session_state.get('full_content', '')} e forneça uma decisão baseada em regras e lógica sobre [tópico_específico]."
                        "Faça uma análise de custo-benefício do arquivo {st.session_state.get('full_content', '')} e forneça uma recomendação sobre a melhor opção."

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
            pdf_content = pdf.output(dest='S').encode('latin-1')
            pdf_buffer.write(pdf_content)
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
