# ============================================================
# analista.py  —  Oráculo Analista  v2.4
# ============================================================
import io
import json
import os
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests
import streamlit as st
from decouple import config
from docx import Document
from PyPDF2 import PdfReader

from src.runtime import Runtime
from src.cost_tracker import render_cost_widget
from src.constants.settings import MAX_TOKENS_FREE_PLAN, DEFAULT_MODEL


# =========================
# Configurações
# =========================
PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

icons = {
    "assistant": "./src/img/perfil-analista.png",
    "user":      "./src/img/usuario.jpg",
}

CSS_GLOBAL = """
<style>
.highlight-creme  {
    background: linear-gradient(90deg,#f5f5dc,gold);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-weight:bold;
}
.highlight-dourado{
    background: linear-gradient(90deg,gold,#f5f5dc);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-weight:bold;
}
@keyframes pulseGold {
    0%   { opacity:1;    letter-spacing:0.12em; text-shadow:0 0 0px gold; }
    50%  { opacity:0.80; letter-spacing:0.18em; text-shadow:0 0 16px gold,0 0 32px #ffd70088; }
    100% { opacity:1;    letter-spacing:0.12em; text-shadow:0 0 0px gold; }
}
.upload-label {
    display:block;
    font-size:1.55rem;
    font-weight:900;
    letter-spacing:0.12em;
    text-transform:uppercase;
    background:linear-gradient(90deg,gold 0%,#fffbe6 50%,gold 100%);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation:pulseGold 2.4s ease-in-out infinite;
    margin-bottom:0.55rem;
    user-select:none;
}
</style>
"""


# =========================
# Truncate local seguro
# =========================
def _truncate(text, limite: int = 10_000) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limite:
        return text
    return text[:limite] + f"\n\n[... truncado após {limite} caracteres ...]"


# =========================
# Runtime singleton por sessão
# =========================
def get_runtime() -> Runtime:
    if "_runtime" not in st.session_state:
        st.session_state["_runtime"] = Runtime(
            api_key=config("GROQ_API_KEY", default=""),
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS_FREE_PLAN,
        )
    return st.session_state["_runtime"]


# =========================
# Contexto dos arquivos
# =========================
def obter_resumo_arquivos(arquivos: list) -> str:
    blocos = []
    for arq in arquivos:
        nome  = arq.get("name", "arquivo")
        tipo  = arq.get("type", "?")
        pags  = arq.get("pages")
        texto = _truncate(arq.get("text") or "", 6000)
        meta  = f"Arquivo: {nome} | Tipo: {tipo}"
        if pags:
            meta += f" | Páginas: {pags}"
        blocos.append(f"{meta}\n{texto}")
    return "\n\n".join(blocos)


def responder_pergunta_simples(prompt: str, arquivos: list):
    prompt_lower = prompt.lower().strip()
    if any(p in prompt_lower for p in
           ["quantas páginas", "numero de páginas", "número de páginas"]):
        pdfs = [a for a in arquivos
                if a.get("type") == "pdf" and a.get("pages") is not None]
        if len(pdfs) == 1:
            return f"O documento {pdfs[0]['name']} possui {pdfs[0]['pages']} páginas."
        elif len(pdfs) > 1:
            return "Documentos PDF:\n" + "\n".join(
                f"{p['name']}: {p['pages']} páginas" for p in pdfs
            )
    return None


# =========================
# Sessão e usuário
# =========================
def atualizar_primeiro_nome() -> None:
    user = st.session_state.get("user")
    if user and getattr(user, "name", None):
        st.session_state["primeiro_nome"] = user.name.strip().split()[0]


def obter_avatar_usuario() -> str:
    user = st.session_state.get("user")
    if (user and getattr(user, "profile_image_path", None)
            and os.path.exists(user.profile_image_path)):
        return user.profile_image_path
    return "./src/img/usuario.jpg"


# =========================
# Leitores de arquivo
# =========================
def read_xlsx(file) -> dict:
    text = ""
    try:
        with pd.ExcelFile(file) as xls:
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                text += f"--- Aba: {sheet} ---\n{df.to_string()}\n\n"
    except Exception as e:
        text = f"Erro ao ler XLSX: {e}"
    return {"text": text or "", "pages": None, "type": "xlsx"}


def read_pdf(file) -> dict:
    try:
        reader     = PdfReader(file)
        total_pags = len(reader.pages)
        text       = "".join((p.extract_text() or "") + "\n" for p in reader.pages)
    except Exception as e:
        return {"text": f"Erro ao ler PDF: {e}", "pages": None, "type": "pdf"}
    return {"text": text or "", "pages": total_pags, "type": "pdf"}


def read_json(file) -> dict:
    try:
        text = json.dumps(json.load(file), indent=4, ensure_ascii=False)
    except Exception as e:
        text = f"Erro ao ler JSON: {e}"
    return {"text": text or "", "pages": None, "type": "json"}


def read_xml(file) -> dict:
    try:
        tree = ET.parse(file)
        text = ET.tostring(tree.getroot(), encoding="utf-8").decode()
    except Exception as e:
        text = f"Erro ao ler XML: {e}"
    return {"text": text or "", "pages": None, "type": "xml"}


def read_html(file) -> dict:
    try:
        text = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        text = f"Erro ao ler HTML: {e}"
    return {"text": text or "", "pages": None, "type": "html"}


def read_docx(file) -> dict:
    try:
        doc  = Document(file)
        text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        text = f"Erro ao ler DOCX: {e}"
    return {"text": text or "", "pages": None, "type": "docx"}


def read_txt(file) -> dict:
    try:
        text = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        text = f"Erro ao ler TXT: {e}"
    return {"text": text or "", "pages": None, "type": "txt"}


def processar_arquivo(file) -> dict:
    t = file.type
    if t in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ):
        res = read_xlsx(file)
    elif t == "application/pdf":
        res = read_pdf(file)
    elif t == "application/json":
        res = read_json(file)
    elif t in ("application/xml", "text/xml"):
        res = read_xml(file)
    elif t in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        res = read_docx(file)
    elif t == "text/plain":
        res = read_txt(file)
    elif t in ("text/html", "text/htm"):
        res = read_html(file)
    else:
        try:
            text = file.read().decode("utf-8", errors="replace")
        except Exception:
            text = "Tipo de arquivo não suportado."
        res = {"text": text, "pages": None, "type": "unknown"}
    res["name"] = file.name
    if not isinstance(res.get("text"), str):
        res["text"] = str(res.get("text", ""))
    return res


# =========================
# Dialog de instruções
# =========================
@st.dialog("💡 Como usar o Oráculo Analista", width="large")
def dialog_instrucoes():
    st.markdown("""
    ### 🚀 Bem-vindo ao Oráculo Analista!

    ---

    #### 📂 1. Carregar Documentos
    - Clique em **"Browse files"** na área **📂 CARREGAR ARQUIVOS**.
    - Formatos aceitos: `PDF`, `XLSX`, `XLS`, `DOCX`, `DOC`, `TXT`, `JSON`, `XML`, `HTML`.
    - Você pode carregar **múltiplos arquivos** ao mesmo tempo.

    #### 🔍 2. Fazer a Leitura
    - Após selecionar os arquivos, clique em **🔍 FAZER LEITURA**.
    - O Oráculo irá ler e compreender o conteúdo de todos os documentos.

    #### 💬 3. Fazer Perguntas
    - Use o chat abaixo para perguntar sobre os documentos carregados.
    - Exemplos: *"Faça um resumo"*, *"Quais os pontos principais?"*

    #### 📊 4. Exportar
    - Use **📊 Baixar em Excel** ou **📄 Baixar em PDF** para salvar a conversa.

    #### 🔄 5. Limpar
    - Botão **🔄 Limpar Conversa** na barra lateral reinicia a sessão.

    ---
    > ⚠️ Faça perguntas objetivas para melhores resultados.
    """)
    if st.button("✅ Entendido!", use_container_width=True):
        st.rerun()


# =========================
# Seção CARREGAR ARQUIVOS + FAZER LEITURA
# =========================
def secao_upload_e_leitura() -> None:
    st.markdown(
        '<span class="upload-label">📂 Carregar Arquivos</span>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "",
        type=["xlsx", "pdf", "xml", "json", "html", "htm",
              "doc", "docx", "txt", "xls"],
        accept_multiple_files=True,
        key="main_uploader",
        label_visibility="collapsed",
    )

    if st.button("🔍 FAZER LEITURA", key="btn_fazer_leitura", type="primary"):
        if not uploaded:
            st.warning("⚠️ Selecione ao menos um arquivo antes de fazer a leitura.")
            return

        processados = []
        erros       = []
        with st.spinner("🔎 Oráculo Analista lendo e compreendendo os documentos..."):
            for f in uploaded:
                try:
                    processados.append(processar_arquivo(f))
                except Exception as e:
                    erros.append(f"{f.name}: {e}")

        if erros:
            st.error("Erro em alguns arquivos:\n" + "\n".join(erros))

        if not processados:
            return

        st.session_state["arquivos_processados"] = processados
        st.session_state["full_content"]         = obter_resumo_arquivos(processados)

        # Apenas mensagem no chat — sem st.success e sem prévia
        msg_leitura = (
            f"📚 Li e analisei {len(processados)} documento(s).\n\n"
            "Agora você pode me fazer perguntas sobre o conteúdo. Como posso ajudar? 💡"
        )
        st.session_state.setdefault("messages", []).append(
            {"role": "assistant", "content": msg_leitura}
        )
        st.rerun()


# =========================
# Intenção do usuário
# =========================
def verificar_intencao_usuario(prompt: str):
    p = prompt.lower()
    if any(k in p for k in [
        "plano", "assinar", "upgrade", "mensal",
        "trimestral", "anual", "contratar", "preço",
    ]):
        return "plano"
    if any(k in p for k in [
        "reunião", "agendar", "consultoria",
        "falar com o desenvolvedor", "encontro",
    ]):
        return "reuniao"
    return None


# =========================
# Formulários de intenção
# =========================
def mostrar_formulario_plano() -> None:
    st.markdown("💡 Percebi que você está interessado em nossos planos!")
    with st.form("form_planos", clear_on_submit=True):
        st.markdown("### 💼 Planos Oráculo Analista")
        col1, col2 = st.columns(2)
        with col1:
            plano = st.selectbox(
                "Selecione um plano:",
                ["Mensal - R$ 49,90", "Trimestral - R$ 119,90", "Anual - R$ 369,90"],
            )
        with col2:
            links = {
                "Mensal - R$ 49,90":      ("Assinar Mensal",     "https://sandbox.asaas.com/c/qmo94xid8f1i6tnc"),
                "Trimestral - R$ 119,90": ("Assinar Trimestral", "https://sandbox.asaas.com/c/jsmak76vdo5fke23"),
                "Anual - R$ 369,90":      ("Assinar Anual",      "https://sandbox.asaas.com/c/adu6nd24lf8jauo3"),
            }
            label, url = links[plano]
            st.link_button(label, url)
        if st.form_submit_button("Confirmar plano"):
            st.success("✅ Plano selecionado!")
            st.balloons()


def mostrar_formulario_reuniao() -> None:
    st.markdown("📅 Preencha os dados para agendar uma reunião:")
    with st.form("form_agendamento", clear_on_submit=True):
        nome     = st.text_input("Nome completo")
        empresa  = st.text_input("Empresa (opcional)")
        whatsapp = st.text_input("WhatsApp")
        email    = st.text_input("E-mail")
        data     = st.date_input("Data")
        hora     = st.time_input("Horário")
        if st.form_submit_button("Agendar"):
            webhook = config("WEBHOOK_AGENDA_ANALISTA", default="")
            payload = {
                "nome": nome, "empresa": empresa,
                "whatsapp": whatsapp, "email": email,
                "data": str(data), "hora": str(hora),
            }
            try:
                r = requests.post(webhook, json=payload, timeout=20)
                if r.status_code == 200:
                    st.success(f"✅ Obrigado {nome}, agendamento realizado!")
                    st.balloons()
                else:
                    st.error("❌ Erro ao enviar agendamento.")
            except Exception as e:
                st.error(f"Erro: {e}")


# =========================
# Interface principal
# =========================
def oraculo_analista() -> None:
    atualizar_primeiro_nome()
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

    # Título
    st.markdown(
        "<h1 class='title'>Análise rápida e precisa com o "
        "<span class='highlight-creme'>Oráculo</span> "
        "<span class='highlight-dourado'>Analista</span></h1>",
        unsafe_allow_html=True,
    )

    # Botões: instruções + exportação
    from src.tools.export_tool import ExportTool
    msgs = st.session_state.get("messages", [])
    col_inst, col_exp1, col_exp2 = st.columns([2, 1.5, 1.5])

    with col_inst:
        if st.button("💡 Como usar o Oráculo Analista",
                     use_container_width=True, key="btn_instrucoes"):
            dialog_instrucoes()

    with col_exp1:
        if msgs:
            try:
                excel = ExportTool()(format="excel", messages=msgs)
                st.download_button(
                    "📊 Baixar em Excel", data=excel,
                    file_name="chat_oraculo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_excel_top",
                )
            except Exception as e:
                st.error(f"Erro Excel: {e}")
        else:
            st.button("📊 Baixar em Excel", disabled=True,
                      use_container_width=True, key="dl_excel_dis")

    with col_exp2:
        if msgs:
            try:
                pdf = ExportTool()(format="pdf", messages=msgs)
                st.download_button(
                    "📄 Baixar em PDF", data=io.BytesIO(pdf),
                    file_name="chat_oraculo.pdf", mime="application/pdf",
                    use_container_width=True, key="dl_pdf_top",
                )
            except Exception as e:
                st.error(f"Erro PDF: {e}")
        else:
            st.button("📄 Baixar em PDF", disabled=True,
                      use_container_width=True, key="dl_pdf_dis")

    st.markdown("---")

    # Sidebar
    if os.path.exists("./src/img/perfil-analista.png"):
        st.sidebar.image("./src/img/perfil-analista.png", width=500)

    if st.sidebar.button("🔄 Limpar Conversa"):
        get_runtime().reset_session()
        st.session_state.pop("messages", None)
        st.session_state.pop("arquivos_processados", None)
        st.session_state.pop("full_content", None)
        st.rerun()

    render_cost_widget()

    # Upload + FAZER LEITURA
    secao_upload_e_leitura()

    st.markdown("---")

    # Histórico do chat
    if "messages" not in st.session_state:
        nome = st.session_state.get("primeiro_nome", "Usuário")
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": (
                f"🌟 Olá, {nome}! Sou o Oráculo Analista.\n\n"
                "**Para começar:**\n"
                "1. Selecione seus arquivos em **📂 CARREGAR ARQUIVOS** acima\n"
                "2. Clique em **🔍 FAZER LEITURA** para que eu entenda o conteúdo\n"
                "3. Depois é só me perguntar! 💡"
            ),
        }]

    for msg in st.session_state["messages"]:
        avatar = obter_avatar_usuario() if msg["role"] == "user" else icons["assistant"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Digite sua pergunta aqui:", key="chat_input_analista"):
        avatar   = obter_avatar_usuario()
        intencao = verificar_intencao_usuario(prompt)

        with st.chat_message("user", avatar=avatar):
            st.write(prompt)

        st.session_state.setdefault("messages", []).append(
            {"role": "user", "content": prompt}
        )

        arquivos_sess  = st.session_state.get("arquivos_processados", [])
        resposta_local = responder_pergunta_simples(prompt, arquivos_sess)
        if resposta_local:
            with st.chat_message("assistant", avatar=icons["assistant"]):
                st.write(resposta_local)
            st.session_state["messages"].append(
                {"role": "assistant", "content": resposta_local}
            )
            return

        if intencao:
            time.sleep(1)
            with st.chat_message("assistant", avatar=icons["assistant"]):
                if intencao == "plano":
                    mostrar_formulario_plano()
                else:
                    mostrar_formulario_reuniao()
            return

        with st.chat_message("assistant", avatar=icons["assistant"]):
            try:
                runtime      = get_runtime()
                file_context = st.session_state.get("full_content", "")
                container    = st.empty()

                with st.spinner("Gerando análise..."):
                    def _stream_cb(text: str):
                        container.markdown(text)

                    st.session_state["messages"].pop()
                    response = runtime.run(
                        user_input=prompt,
                        file_context=file_context,
                        stream_callback=_stream_cb,
                    )

                container.markdown(response)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                st.error(f"Erro ao gerar análise: {e}")


if __name__ == "__main__":
    oraculo_analista()
