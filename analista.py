import base64
import io
import json
import os
import re
import time
import xml.etree.ElementTree as ET

import groq
import pandas as pd
import requests
import streamlit as st
from decouple import config
from docx import Document
from fpdf import FPDF
from openpyxl.styles import Alignment, Font, PatternFill
from PyPDF2 import PdfReader


# =========================
# Configurações iniciais
# =========================

def _get_secret_with_source(key, default=""):
    """Retorna valor e origem da configuração, sem expor o segredo."""
    try:
        value = config(key, default=None)
        if value is not None:
            return value, ".env"
    except Exception:
        pass

    value = os.getenv(key)
    if value is not None:
        return value, "os.environ"

    try:
        if key in st.secrets:
            return st.secrets[key], "st.secrets"
    except Exception:
        pass

    try:
        if "groq" in st.secrets and key in st.secrets["groq"]:
            return st.secrets["groq"][key], "st.secrets[groq]"
    except Exception:
        pass

    return default, "nao_encontrada"

def _get_secret(key, default=""):
    """Prioriza .env local e usa st.secrets como fallback no Streamlit Cloud."""
    value, _ = _get_secret_with_source(key, default=default)
    return value


def get_groq_diagnostics():
    _, key_source = _get_secret_with_source("GROQ_API_KEY")
    _, model_source = _get_secret_with_source("GROQ_MODEL", "llama-3.3-70b-versatile")

    diagnostics = [f"GROQ_API_KEY origem: {key_source}"]
    diagnostics.append(f"GROQ_MODEL origem: {model_source}")

    try:
        root_keys = list(st.secrets.keys())
        diagnostics.append(f"st.secrets raiz contem GROQ_API_KEY: {'GROQ_API_KEY' in root_keys}")
        diagnostics.append(f"st.secrets contem secao groq: {'groq' in root_keys}")
    except Exception:
        diagnostics.append("st.secrets indisponivel neste contexto")

    return " | ".join(diagnostics)


def get_groq_api_key():
    return _get_secret("GROQ_API_KEY")


def get_groq_model():
    return _get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")


def validar_groq_config():
    if not get_groq_api_key():
        raise ValueError(
            "GROQ_API_KEY não configurada. Defina a variável no arquivo .env local ou em Streamlit secrets no deploy. "
            + get_groq_diagnostics()
        )


def get_groq_client():
    validar_groq_config()
    from groq import Groq
    return Groq(api_key=get_groq_api_key())


PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

icons = {
    "assistant": "./src/img/perfil-analista.png",
    "user": "./src/img/usuario.jpg",
}


# =========================
# Utilidades de contexto
# =========================
def resumir_texto_para_contexto(texto: str, limite: int = 12000) -> str:
    if not texto:
        return ""
    texto = texto.strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite] + "\n\n[Conteúdo truncado automaticamente por limite de contexto.]"


def obter_resumo_arquivos(arquivos):
    blocos = []

    for arq in arquivos:
        nome = arq.get("name", "arquivo")
        tipo = arq.get("type", "desconhecido")
        paginas = arq.get("pages")
        texto = resumir_texto_para_contexto(arq.get("text", ""), limite=6000)

        meta = f"Arquivo: {nome} | Tipo: {tipo}"
        if paginas is not None:
            meta += f" | Páginas: {paginas}"

        blocos.append(f"{meta}\n{texto}")

    return "\n\n".join(blocos)


def responder_pergunta_simples(prompt: str, arquivos):
    prompt_lower = prompt.lower().strip()

    if (
        "quantas páginas" in prompt_lower
        or "numero de páginas" in prompt_lower
        or "número de páginas" in prompt_lower
    ):
        pdfs = [a for a in arquivos if a.get(
            "type") == "pdf" and a.get("pages") is not None]

        if len(pdfs) == 1:
            return f"O documento {pdfs[0]['name']} possui {pdfs[0]['pages']} páginas."
        elif len(pdfs) > 1:
            resposta = []
            for pdf in pdfs:
                resposta.append(f"{pdf['name']}: {pdf['pages']} páginas")
            return "Documentos PDF carregados:\n" + "\n".join(resposta)

    return None


def montar_historico_reduzido(max_mensagens: int = 6):
    return st.session_state.get("messages", [])[-max_mensagens:]


# =========================
# LLM
# =========================
def generate_groq_response(client, system_prompt, prompt, history=None):
    messages = [{"role": "system", "content": system_prompt}]

    for dict_message in history or []:
        messages.append(
            {"role": dict_message["role"], "content": dict_message["content"]}
        )

    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model=get_groq_model(),
        messages=messages,
        temperature=0.1,
        max_tokens=1200,
        top_p=1,
        stream=True,
    )
    return stream


# =========================
# Sessão e usuário
# =========================
def atualizar_primeiro_nome():
    if "user" in st.session_state and getattr(st.session_state.user, "name", None):
        nome_completo = st.session_state.user.name.strip()
        if nome_completo:
            st.session_state["primeiro_nome"] = nome_completo.split()[0]


def obter_primeiro_nome_usuario() -> str:
    primeiro_nome = st.session_state.get("primeiro_nome")
    if primeiro_nome:
        return primeiro_nome

    user = st.session_state.get("user")
    if user and getattr(user, "name", None):
        nome_completo = user.name.strip()
        if nome_completo:
            primeiro_nome = nome_completo.split()[0]
            st.session_state["primeiro_nome"] = primeiro_nome
            return primeiro_nome

    nome = st.session_state.get("name")
    if nome:
        nome_completo = nome.strip()
        if nome_completo:
            primeiro_nome = nome_completo.split()[0]
            st.session_state["primeiro_nome"] = primeiro_nome
            return primeiro_nome

    return "Usuário"


def atualizar_imagem_perfil(email):
    normalized_email = (email or "").strip().lower().replace("/", "_").replace("\\", "_")
    image_path = os.path.join(PROFILE_IMAGES_DIR, f"{normalized_email}.png")
    if os.path.exists(image_path):
        st.session_state.image = image_path


def configurar_usuario_logado(user):
    st.session_state.name = user.name
    st.session_state.email = user.email
    st.session_state.image = user.profile_image_path
    st.session_state.primeiro_nome = user.name.split(" ")[0]


def obter_avatar_usuario():
    # Tenta session_state.image (definido em configurar_usuario_logado)
    img = st.session_state.get("image")
    if img and os.path.exists(img):
        return img
    # Tenta via objeto user
    user = st.session_state.get("user")
    if user and getattr(user, "profile_image_path", None):
        path = user.profile_image_path
        if os.path.exists(path):
            return path
    # Tenta buscar pelo e-mail do usuário logado
    if user and getattr(user, "email", None):
        normalized_email = user.email.strip().lower().replace("/", "_").replace("\\", "_")
        for email_candidate in [normalized_email, user.email]:
            for ext in (".png", ".jpg", ".jpeg"):
                candidate = os.path.join(PROFILE_IMAGES_DIR, f"{email_candidate}{ext}")
                if os.path.exists(candidate):
                    return candidate
    fallback = "./src/img/usuario.jpg"
    if os.path.exists(fallback):
        return fallback
    return None


# =========================
# Leitores de arquivo
# =========================
def read_xlsx(file):
    text = ""
    with pd.ExcelFile(file) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            text += f"--- Aba: {sheet_name} ---\n{df.to_string()}\n\n"

    return {
        "text": text,
        "pages": None,
        "type": "xlsx",
    }


def read_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    total_pages = len(pdf_reader.pages)

    for page in pdf_reader.pages:
        extracted = page.extract_text() or ""
        text += extracted + "\n"

    return {
        "text": text,
        "pages": total_pages,
        "type": "pdf",
    }


def read_json(file):
    return {
        "text": json.dumps(json.load(file), indent=4, ensure_ascii=False),
        "pages": None,
        "type": "json",
    }


def read_xml(file):
    tree = ET.parse(file)
    return {
        "text": ET.tostring(tree.getroot(), encoding="utf-8").decode("utf-8"),
        "pages": None,
        "type": "xml",
    }


def read_html(file):
    return {
        "text": file.read().decode("utf-8"),
        "pages": None,
        "type": "html",
    }


def read_docx(file):
    doc = Document(file)
    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    return {
        "text": text,
        "pages": None,
        "type": "docx",
    }


def read_txt(file):
    return {
        "text": file.read().decode("utf-8"),
        "pages": None,
        "type": "txt",
    }


# =========================
# Upload para análise
# =========================
def _processar_arquivo(file):
    """Processa um único arquivo e retorna o dicionário de resultado."""
    if file.type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]:
        resultado = read_xlsx(file)
    elif file.type == "application/pdf":
        resultado = read_pdf(file)
    elif file.type == "application/json":
        resultado = read_json(file)
    elif file.type in ["application/xml", "text/xml"]:
        resultado = read_xml(file)
    elif file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        resultado = read_docx(file)
    elif file.type == "text/plain":
        resultado = read_txt(file)
    elif file.type in ["text/html", "text/htm"]:
        resultado = read_html(file)
    else:
        resultado = {
            "text": "Tipo de arquivo não suportado.",
            "pages": None,
            "type": "unknown",
        }
    resultado["name"] = file.name
    return resultado


@st.dialog("� Arquivo Carregado")
def _dialog_arquivo_carregado():
    st.markdown(
        """
        <div style="text-align:center; padding:18px 8px;">
            <p style="font-size:22px; font-weight:700; line-height:1.4; text-transform:uppercase; margin:0;">
                VOCÊ ACABOU DE CARREGAR SEU ARQUIVO!<br>
                AGORA CLIQUE NO BOTÃO LER DOCUMENTO PARA O ORÁCULO ANALISTA
                LER E ENTENDER DO QUE SE TRATA.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("OK, entendi!", use_container_width=True, type="primary"):
        st.session_state.pop("mostrar_dialog_upload", None)
        st.rerun()


@st.dialog("✅ Leitura Concluída")
def _dialog_leitura_concluida():
    # Borda verde ao redor do conteúdo do dialog + mensagem em caixa alta
    st.markdown(
        """
        <style>
            div[role="dialog"] { border: 3px solid #22c55e !important; border-radius: 12px !important; }
        </style>
        <div style="text-align:center; padding:18px 8px; border:3px solid #22c55e;
                    border-radius:10px; background:rgba(34,197,94,0.08);">
            <p style="font-size:22px; font-weight:700; line-height:1.4; text-transform:uppercase; margin:0; color:#15803d;">
                O ORÁCULO ANALISTA FEZ A LEITURA E ENTENDEU TODO O DOCUMENTO
                CARREGADO, INICIE SEU ESTUDO OU ANÁLISE
            </p>
            <p style="margin-top:12px; font-size:13px; color:#16a34a;">
                Esta janela fechará automaticamente em 5 segundos…
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Auto-fechamento após 5 segundos
    time.sleep(5)
    st.session_state.pop("mostrar_dialog_leitura", None)
    st.rerun()


@st.dialog("🔄 Limpar Conversa")
def _dialog_confirmar_limpar():
    st.markdown(
        "Deseja realmente limpar a **conversa**?\n\n"
        "📄 O(s) documento(s) já carregado(s) serão **mantidos** para que você "
        "possa continuar suas análises sem precisar enviá-los novamente."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.pop("confirmar_limpar", None)
            st.rerun()
    with col_b:
        if st.button("🧹 Sim, limpar", use_container_width=True, type="primary"):
            # Limpa apenas as mensagens do chat; documentos permanecem ativos
            st.session_state.messages = []
            st.session_state.pop("confirmar_limpar", None)
            st.rerun()


def _on_upload_change():
    """Callback do file_uploader: dispara o dialog de orientação após upload."""
    arquivos = st.session_state.get("uploader_analista") or []
    if arquivos:
        nomes = [getattr(a, "name", "") for a in arquivos]
        # Só mostra o dialog quando um conjunto novo de arquivos é carregado
        if st.session_state.get("_ultimos_uploads") != nomes:
            st.session_state["_ultimos_uploads"] = nomes
            st.session_state["mostrar_dialog_upload"] = True


def carregar_arquivos():
    """Upload e leitura de documentos na área principal."""
    col_upload, col_ler, col_limpar = st.columns([2, 1, 1])

    with col_upload:
        st.markdown(
            "<div class='titulo-carregar-arquivo'>📁 CARREGAR ARQUIVO</div>",
            unsafe_allow_html=True,
        )
        uploaded_files = st.file_uploader(
            "📎 Upload do documento",
            type=["xlsx", "pdf", "xml", "json", "html",
                  "htm", "doc", "docx", "txt", "xls"],
            accept_multiple_files=True,
            key="uploader_analista",
            on_change=_on_upload_change,
            label_visibility="collapsed",
        )

    with col_ler:
        btn_ler = st.button("📖 LER DOCUMENTO", use_container_width=True, type="primary")

    with col_limpar:
        btn_limpar = st.button("🔄 Limpar Conversa", use_container_width=True)

    if btn_limpar:
        # Limpa SOMENTE a conversa; mantém arquivos carregados/lidos
        st.session_state["confirmar_limpar"] = True

    if st.session_state.get("confirmar_limpar"):
        _dialog_confirmar_limpar()

    arquivos_processados = []

    if btn_ler:
        if not uploaded_files:
            st.warning("Nenhum arquivo foi selecionado. Faça o upload primeiro.")
            return arquivos_processados

        with st.spinner("Lendo documento(s)..."):
            for file in uploaded_files:
                resultado = _processar_arquivo(file)
                arquivos_processados.append(resultado)

        # Salva no session_state antes do rerun para persistir os dados
        st.session_state.arquivos_processados = arquivos_processados
        st.session_state.full_content = obter_resumo_arquivos(arquivos_processados)
        st.session_state.mostrar_dialog_leitura = True
        # Garante que o dialog de "upload" não apareça por cima
        st.session_state.pop("mostrar_dialog_upload", None)
        st.rerun()

    # Dialog logo após o upload (antes da leitura)
    if st.session_state.get("mostrar_dialog_upload"):
        _dialog_arquivo_carregado()

    # Dialog após leitura concluída (com borda verde, fecha em 5s)
    if st.session_state.get("mostrar_dialog_leitura"):
        _dialog_leitura_concluida()

    return arquivos_processados


# =========================
# Intenção do usuário
# =========================
def verificar_intencao_usuario(prompt):
    prompt = prompt.lower()

    if any(
        p in prompt
        for p in ["plano", "assinar", "upgrade", "mensal", "trimestral", "anual", "contratar", "preço"]
    ):
        return "plano"

    if any(
        p in prompt
        for p in ["reunião", "agendar", "consultoria", "falar com o desenvolvedor", "encontro"]
    ):
        return "reuniao"

    if any(
        p in prompt
        for p in [
            "finalizar", "encerrar", "terminei", "concluir", "acabou",
            "pronto", "é isso", "obrigado", "obrigada", "valeu",
            "baixar", "exportar", "download", "salvar conversa",
            "gerar pdf", "gerar excel", "fim", "tchau", "até mais",
        ]
    ):
        return "finalizar"

    return None


# =========================
# Exportação
# =========================
def gerar_excel_conversa(df: pd.DataFrame) -> bytes:
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Conversa", index=False)

        worksheet = writer.sheets["Conversa"]

        header_fill = PatternFill(fill_type="solid", fgColor="D7E4BC")
        header_font = Font(bold=True)
        header_alignment = Alignment(vertical="top", wrap_text=True)

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                try:
                    cell_value = str(
                        cell.value) if cell.value is not None else ""
                    if len(cell_value) > max_length:
                        max_length = len(cell_value)
                except Exception:
                    pass

            worksheet.column_dimensions[column_letter].width = min(
                max(max_length + 2, 20), 60)

    excel_buffer.seek(0)
    return excel_buffer.getvalue()


def gerar_pdf_conversa(chat_text: list[dict]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Oráculo Analista - Histórico de Conversa",
             ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=12)

    def remover_emojis(texto):
        return re.sub(r"[^\x00-\x7F]+", "", texto)

    for m in chat_text:
        role = remover_emojis(m["role"].capitalize())
        content = remover_emojis(m["content"])
        pdf.multi_cell(0, 10, f"{role}: {content}", border=0)

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1", errors="ignore")
    return bytes(output)


# =========================
# Interface principal
# =========================
def oraculo_analista():

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
        /* Avatar circular com borda neon pulsante */
        .oraculo-avatar-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 18px 0 24px 0;
        }
        .oraculo-avatar {
            width: 220px;
            height: 220px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #00f0ff;
            box-shadow:
                0 0 12px #00f0ff,
                0 0 24px #00f0ff,
                0 0 48px #00f0ff,
                inset 0 0 18px rgba(0, 240, 255, 0.45);
            animation: oraculo-neon-pulse 2.4s ease-in-out infinite;
        }
        @keyframes oraculo-neon-pulse {
            0%, 100% {
                box-shadow:
                    0 0 10px #00f0ff,
                    0 0 20px #00f0ff,
                    0 0 40px #00f0ff,
                    inset 0 0 14px rgba(0, 240, 255, 0.35);
            }
            50% {
                box-shadow:
                    0 0 18px #39ff14,
                    0 0 36px #39ff14,
                    0 0 64px #39ff14,
                    inset 0 0 22px rgba(57, 255, 20, 0.45);
                border-color: #39ff14;
            }
        }
        /* Título "CARREGAR ARQUIVO" */
        .titulo-carregar-arquivo {
            text-align: center;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 2px;
            color: #22c55e;
            text-transform: uppercase;
            margin: 4px 0 8px 0;
            text-shadow: 0 0 6px rgba(34, 197, 94, 0.55);
        }
        /* Borda verde no file_uploader */
        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploaderDropzone"] {
            border: 2px solid #22c55e !important;
            border-radius: 10px !important;
            box-shadow: 0 0 8px rgba(34, 197, 94, 0.45);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    avatar_path = "./src/img/perfil-analista.png"
    if os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as _f:
                _avatar_b64 = base64.b64encode(_f.read()).decode("utf-8")
            st.markdown(
                f"<div class='oraculo-avatar-wrapper'>"
                f"<img class='oraculo-avatar' src='data:image/png;base64,{_avatar_b64}' alt='Oráculo Analista'/>"
                f"</div>",
                unsafe_allow_html=True,
            )
        except Exception:
            pass

    if os.path.exists("./src/img/perfil-analista.png"):
        st.sidebar.image("./src/img/perfil-analista.png", width=500)

    arquivos = carregar_arquivos()

    if "messages" not in st.session_state:
        primeiro_nome = obter_primeiro_nome_usuario()
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f'🌟 {primeiro_nome}, estou aqui para te ajudar a analisar ou fazer estudo sobre seus documentos. Faça o upload de um documento acima e clique em **📖 LER DOCUMENTO** para iniciar 💡',
            }
        ]

    for message in st.session_state.messages:
        avatar_image = (
            obter_avatar_usuario(
            ) if message["role"] == "user" else icons["assistant"]
        )
        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])

    if prompt := st.chat_input("Digite sua pergunta aqui:", key="chat_input_analista"):
        avatar_image = obter_avatar_usuario()
        intencao = verificar_intencao_usuario(prompt)

        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        arquivos = st.session_state.get("arquivos_processados", [])
        resposta_local = responder_pergunta_simples(prompt, arquivos)

        if resposta_local:
            with st.chat_message("assistant", avatar=icons["assistant"]):
                st.write(resposta_local)

            st.session_state.messages.append(
                {"role": "assistant", "content": resposta_local}
            )
            return

        if intencao in ["plano", "reuniao", "finalizar"]:
            time.sleep(3)

            if intencao == "plano":
                with st.chat_message("assistant", avatar=icons["assistant"]):
                    st.markdown(
                        "💡 Percebi que você está interessado em nossos planos! Veja as opções abaixo:")

                    with st.form("form_planos", clear_on_submit=True):
                        st.markdown("### 💼 Planos Oráculo Analista")
                        st.write(
                            "Escolha um dos planos abaixo para liberar recursos avançados.")

                        col1, col2 = st.columns(2)
                        with col1:
                            plano = st.selectbox(
                                "Selecione um plano:",
                                [
                                    "Mensal - R$ 49,90",
                                    "Trimestral - R$ 119,90",
                                    "Anual - R$ 369,90",
                                ],
                                key="plano_escolhido",
                            )

                        with col2:
                            if plano == "Mensal - R$ 49,90":
                                st.write(
                                    "Ideal para quem deseja experimentar nossos serviços por um curto período.")
                                st.link_button(
                                    "Assinar Mensal", "https://sandbox.asaas.com/c/qmo94xid8f1i6tnc")
                            elif plano == "Trimestral - R$ 119,90":
                                st.write(
                                    "Economize em relação ao plano mensal e tenha mais tempo para aproveitar.")
                                st.link_button(
                                    "Assinar Trimestral", "https://sandbox.asaas.com/c/jsmak76vdo5fke23")
                            elif plano == "Anual - R$ 369,90":
                                st.write(
                                    "A melhor opção para quem deseja um compromisso a longo prazo com descontos significativos.")
                                st.link_button(
                                    "Assinar Anual", "https://sandbox.asaas.com/c/adu6nd24lf8jauo3")

                        assinar = st.form_submit_button("Confirmar plano")

                    if assinar:
                        st.success(
                            "✅ Plano selecionado com sucesso! Você será redirecionado para concluir sua assinatura.")
                        st.balloons()

            if intencao == "reuniao":
                with st.chat_message("assistant", avatar=icons["assistant"]):
                    st.markdown(
                        "📅 Parece que você deseja agendar uma reunião! Preencha as informações abaixo:")
                    st.markdown(
                        "Assim que você finalizar o cadastro de agendamento você receberá uma confirmação em seu e-mail.")

                    with st.form("form_agendamento", clear_on_submit=True):
                        nome = st.text_input(
                            "Nome completo", key="nome_agendamento")
                        empresa = st.text_input(
                            "Empresa (opcional)", key="empresa_agendamento")
                        whatsapp = st.text_input(
                            "WhatsApp", key="whatsapp_agendamento")
                        email = st.text_input(
                            "E-mail", key="email_agendamento")
                        data = st.date_input("Data", key="data_agendamento")
                        hora = st.time_input("Horário", key="hora_agendamento")

                        agendar = st.form_submit_button("Agendar")

                    if agendar:
                        webhook_agenda = config(
                            "WEBHOOK_AGENDA_ANALISTA", default="")

                        dados_agenda = {
                            "nome": nome,
                            "empresa": empresa,
                            "whatsapp": whatsapp,
                            "email": email,
                            "data": str(data),
                            "hora": str(hora),
                        }

                        try:
                            resposta = requests.post(
                                webhook_agenda, json=dados_agenda, timeout=20)
                            if resposta.status_code == 200:
                                st.success(
                                    f"✅ Obrigado {nome}, seu agendamento foi realizado com sucesso!")
                                st.info(
                                    "Você receberá um e-mail com a confirmação do seu agendamento.")
                                st.balloons()
                            else:
                                st.error(
                                    "❌ Erro ao enviar agendamento para o Oráculo Analista.")
                        except Exception as e:
                            st.error(f"Erro ao enviar para Webhook: {e}")

            if intencao == "finalizar":
                with st.chat_message("assistant", avatar=icons["assistant"]):
                    primeiro_nome = obter_primeiro_nome_usuario()
                    msg_final = f"😊 {primeiro_nome}, foi um prazer te ajudar! Você pode baixar o histórico da conversa nos formatos abaixo:"
                    st.markdown(msg_final)

                st.session_state.messages.append(
                    {"role": "assistant", "content": msg_final}
                )

                # Fim da sessão: descarta os documentos carregados/lidos
                st.session_state["arquivos_processados"] = []
                st.session_state["full_content"] = ""
                st.session_state.pop("_ultimos_uploads", None)

                chat_text = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state["messages"]
                ]
                df = pd.DataFrame(chat_text)

                col_excel, col_pdf = st.columns(2)
                with col_excel:
                    try:
                        excel_bytes = gerar_excel_conversa(df)
                        st.download_button(
                            "📊 Baixar conversa em Excel",
                            data=excel_bytes,
                            file_name="chat_oraculo.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar Excel: {e}")

                with col_pdf:
                    try:
                        pdf_bytes = gerar_pdf_conversa(chat_text)
                        pdf_buffer = io.BytesIO(pdf_bytes)
                        pdf_buffer.seek(0)
                        st.download_button(
                            "📄 Baixar conversa em PDF",
                            data=pdf_buffer,
                            file_name="chat_oraculo.pdf",
                            mime="application/pdf",
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {e}")

        else:
            with st.chat_message("assistant", avatar=icons["assistant"]):
                try:
                    arquivos = st.session_state.get("arquivos_processados", [])
                    contexto_resumido = obter_resumo_arquivos(arquivos)
                    historico_reduzido = montar_historico_reduzido(
                        max_mensagens=6)

                    system_prompt = f"""
                    Você é o Oráculo Analista, doutor e especialista em análise de dados.
                    Sua missão é responder com objetividade, precisão e clareza.
                    Use prioritariamente os metadados e o resumo dos documentos abaixo.
                    Se a informação não estiver disponível no contexto resumido, diga isso claramente.

                    O nome do usuário que está conversando com você é {obter_primeiro_nome_usuario()}.
                    Sempre chame o usuário pelo primeiro nome de forma amigável e cordial nas suas respostas.

                    Resumo dos documentos carregados:
                    {resumir_texto_para_contexto(contexto_resumido, limite=12000)}
                    """

                    client = get_groq_client()
                    full_response = ""
                    clean_response = ""

                    with st.spinner("Gerando análise..."):
                        response_container = st.empty()
                        stream = generate_groq_response(
                            client,
                            system_prompt,
                            prompt,
                            history=historico_reduzido,
                        )

                        for event in stream:
                            if hasattr(event, "choices") and event.choices:
                                delta = event.choices[0].delta.content or ""
                                full_response += delta
                                clean_response = re.sub(
                                    r"<think>.*?</think>", "", full_response, flags=re.DOTALL
                                ).strip()
                                response_container.markdown(clean_response)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": clean_response}
                    )

                except Exception as e:
                    st.error(f"Erro ao gerar análise: {str(e)}")


if __name__ == "__main__":
    oraculo_analista()
