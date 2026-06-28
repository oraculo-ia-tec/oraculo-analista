# ============================================================
# analista.py  —  Oráculo Analista  v3.0
# ============================================================
import io
import json
import os
import time
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st
from docx import Document
from PyPDF2 import PdfReader

from src.runtime import Runtime
from src.cost_tracker import render_cost_widget
from src.constants.settings import MAX_TOKENS_FREE_PLAN, DEFAULT_MODEL
from src.utils.helpers import truncate
from src.styles.theme import apply_global_theme
from agenda_analista import AgendaAnalista

GROQ_API_KEY = st.secrets["groq"]["GROQ_API_KEY"]
GROQ_MODEL   = st.secrets["groq"]["GROQ_MODEL"]

PROFILE_IMAGES_DIR = "./user_profiles/"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

icons = {
    "assistant": "./src/img/perfil-analista.png",
    "user":      "./src/img/usuario.jpg",
}

_agenda = AgendaAnalista()


# ── CSS dos botões animados ────────────────────────────
BOTOES_CSS = """
<style>
@keyframes pulse-blue  { 0%,100%{box-shadow:0 0 0 0 rgba(59,130,246,.6)} 50%{box-shadow:0 0 0 10px rgba(59,130,246,0)} }
@keyframes pulse-green { 0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.6)}  50%{box-shadow:0 0 0 10px rgba(34,197,94,0)}  }
@keyframes pulse-amber { 0%,100%{box-shadow:0 0 0 0 rgba(251,191,36,.6)} 50%{box-shadow:0 0 0 10px rgba(251,191,36,0)} }

.btn-como-usar  { animation:pulse-blue  2s infinite; border:2px solid #3b82f6 !important; border-radius:12px !important; }
.btn-carregar   { animation:pulse-green 2s infinite; border:2px solid #22c55e !important; border-radius:12px !important; }
.btn-ler        { animation:pulse-amber 2s infinite; border:2px solid #fbbf24 !important; border-radius:12px !important; }
</style>
"""


def _injetar_css_botoes() -> None:
    st.markdown(BOTOES_CSS, unsafe_allow_html=True)
    # Aplica classes via JS (compat Streamlit)
    st.markdown("""
    <script>
    const btns = window.parent.document.querySelectorAll('button[kind="secondary"]');
    const labels = ['Como Usar', 'Carregar Arquivos', 'Ler Arquivos'];
    const classes = ['btn-como-usar', 'btn-carregar', 'btn-ler'];
    btns.forEach(b => {
        const idx = labels.indexOf(b.innerText.trim());
        if (idx >= 0) b.classList.add(classes[idx]);
    });
    </script>
    """, unsafe_allow_html=True)


# ── diálogos ─────────────────────────────────────────
@st.dialog("📖 Como Usar o Oráculo Analista")
def _dialog_como_usar() -> None:
    st.markdown("""
### Passo a passo

1. **📤 Carregar Arquivos** — Clique em *Carregar Arquivos* e selecione PDF, Excel, Word, JSON ou TXT
2. **📚 Ler Arquivos** — Clique em *Ler Arquivos* para que o Oráculo processe o conteúdo
3. **❓ Fazer sua pergunta** — Digite sua dúvida no chat e pressione Enter
4. **📊 Receba a análise** — O Oráculo responde com resposta direta, análise, insight e próximo passo
5. **📥 Exportar** — Baixe a conversa em Excel ou PDF pelos botões ao final da página

### Tipos de arquivo suportados
| Tipo | Extensões |
|---|---|
| Planilhas | `.xlsx`, `.xls` |
| Documentos | `.pdf`, `.docx`, `.doc`, `.txt` |
| Dados | `.json`, `.xml`, `.html` |

### Dicas
- Carregue múltiplos arquivos de uma vez para análise comparativa
- Seja específico nas perguntas para respostas mais precisas
- Use *Limpar Conversa* para iniciar uma nova sessão de análise
    """)
    if st.button("Entendido! ✨", use_container_width=True):
        st.rerun()


@st.dialog("✅ Arquivos lidos com sucesso!")
def _dialog_leitura_ok(nomes: list[str]) -> None:
    st.success(f"📚 **{len(nomes)} arquivo(s)** processado(s) e carregado(s) na memória do Oráculo.")
    for n in nomes:
        st.markdown(f"- `{n}`")
    st.markdown("_Este diálogo fecha em 3 segundos..._")
    time.sleep(3)
    st.rerun()


# ── runtime ──────────────────────────────────────────
def get_runtime() -> Runtime:
    if "_runtime" not in st.session_state:
        st.session_state["_runtime"] = Runtime(
            api_key=GROQ_API_KEY,
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS_FREE_PLAN,
        )
    return st.session_state["_runtime"]


# ── utilidades de contexto ─────────────────────────────
def obter_resumo_arquivos(arquivos: list) -> str:
    blocos = []
    for arq in arquivos:
        nome  = arq.get("name", "arquivo")
        tipo  = arq.get("type", "?")
        pags  = arq.get("pages")
        texto = truncate(arq.get("text", ""), limite=6000)
        meta  = f"Arquivo: {nome} | Tipo: {tipo}"
        if pags:
            meta += f" | Páginas: {pags}"
        blocos.append(f"{meta}\n{texto}")
    return "\n\n".join(blocos)


def responder_pergunta_simples(prompt: str, arquivos: list) -> str | None:
    prompt_lower = prompt.lower().strip()
    if any(p in prompt_lower for p in ["quantas páginas", "numero de páginas", "número de páginas"]):
        pdfs = [a for a in arquivos if a.get("type") == "pdf" and a.get("pages") is not None]
        if len(pdfs) == 1:
            return f"O documento {pdfs[0]['name']} possui {pdfs[0]['pages']} páginas."
        elif len(pdfs) > 1:
            return "Documentos PDF carregados:\n" + "\n".join(
                f"{p['name']}: {p['pages']} páginas" for p in pdfs
            )
    return None


def atualizar_primeiro_nome() -> None:
    user = st.session_state.get("user")
    if user and getattr(user, "name", None):
        st.session_state["primeiro_nome"] = user.name.strip().split()[0]


def obter_avatar_usuario() -> str:
    user = st.session_state.get("user")
    if user and getattr(user, "profile_image_path", None) and os.path.exists(user.profile_image_path):
        return user.profile_image_path
    return "./src/img/usuario.jpg"


# ── leitores de arquivo ─────────────────────────────────
def read_xlsx(file) -> dict:
    text = ""
    with pd.ExcelFile(file) as xls:
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            text += f"--- Aba: {sheet} ---\n{df.to_string()}\n\n"
    return {"text": text, "pages": None, "type": "xlsx"}

def read_pdf(file) -> dict:
    reader = PdfReader(file)
    total  = len(reader.pages)
    text   = "".join((p.extract_text() or "") + "\n" for p in reader.pages)
    return {"text": text, "pages": total, "type": "pdf"}

def read_json(file) -> dict:
    return {"text": json.dumps(json.load(file), indent=4, ensure_ascii=False), "pages": None, "type": "json"}

def read_xml(file) -> dict:
    tree = ET.parse(file)
    return {"text": ET.tostring(tree.getroot(), encoding="utf-8").decode(), "pages": None, "type": "xml"}

def read_html(file) -> dict:
    return {"text": file.read().decode("utf-8"), "pages": None, "type": "html"}

def read_docx(file) -> dict:
    doc  = Document(file)
    text = "\n".join(p.text for p in doc.paragraphs)
    return {"text": text, "pages": None, "type": "docx"}

def read_txt(file) -> dict:
    return {"text": file.read().decode("utf-8"), "pages": None, "type": "txt"}


def _processar_arquivo(file) -> dict:
    t = file.type
    if t in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"):
        res = read_xlsx(file)
    elif t == "application/pdf":
        res = read_pdf(file)
    elif t == "application/json":
        res = read_json(file)
    elif t in ("application/xml", "text/xml"):
        res = read_xml(file)
    elif t in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"):
        res = read_docx(file)
    elif t == "text/plain":
        res = read_txt(file)
    elif t in ("text/html", "text/htm"):
        res = read_html(file)
    else:
        res = {"text": "Tipo não suportado.", "pages": None, "type": "unknown"}
    res["name"] = file.name
    return res


# ── intenção + formulários ──────────────────────────────
def verificar_intencao_usuario(prompt: str) -> str | None:
    p = prompt.lower()
    if any(k in p for k in ["plano", "assinar", "upgrade", "mensal", "trimestral", "anual", "contratar", "preço"]):
        return "plano"
    if AgendaAnalista.detectar_intencao(prompt):
        return "reuniao"
    return None


def mostrar_formulario_plano() -> None:
    st.markdown("💡 Percebi que você está interessado em nossos planos! Veja as opções abaixo:")
    from src.payments.plans import PLANOS
    with st.form("form_planos", clear_on_submit=True):
        st.markdown("### 💼 Planos Oráculo Analista")
        col1, col2 = st.columns(2)
        with col1:
            plano_sel = st.selectbox(
                "Selecione um plano:",
                list(PLANOS.keys()),
                format_func=lambda k: f"{PLANOS[k]['label']} - R$ {PLANOS[k]['preco']:.2f}",
            )
        with col2:
            st.link_button(f"Assinar {PLANOS[plano_sel]['label']}", PLANOS[plano_sel]["link"])
        if st.form_submit_button("Confirmar plano"):
            st.success("✅ Plano selecionado! Você será redirecionado para concluir a assinatura.")
            st.balloons()


def botoes_exportacao() -> None:
    from src.tools.export_tool import ExportTool
    msgs = st.session_state.get("messages", [])
    if not msgs:
        return
    exp = ExportTool()
    try:
        excel = exp(format="excel", messages=msgs)
        st.download_button("📊 Baixar conversa em Excel", data=excel,
                           file_name="chat_oraculo.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")
    try:
        pdf_bytes = exp(format="pdf", messages=msgs)
        st.download_button("📄 Baixar conversa em PDF", data=io.BytesIO(pdf_bytes),
                           file_name="chat_oraculo.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")


# ── interface principal ─────────────────────────────────
def oraculo_analista() -> None:
    atualizar_primeiro_nome()
    apply_global_theme()
    _injetar_css_botoes()

    st.markdown(
        "<h1 class='oa-title' style='font-size:2rem;text-align:left;'>Análise rápida e precisa com o "
        "<span class='oa-gradient-creme'>Oráculo</span> "
        "<span class='oa-gradient-ouro'>Analista</span></h1>",
        unsafe_allow_html=True,
    )

    # ── Botões animados ────────────────────────────────
    col_b1, col_b2, col_b3 = st.columns(3)

    with col_b1:
        if st.button("📖 Como Usar", use_container_width=True, key="btn_como_usar"):
            _dialog_como_usar()

    with col_b2:
        uploaded_files = st.file_uploader(
            "📤 Carregar Arquivos",
            type=["xlsx","pdf","xml","json","html","htm","doc","docx","txt","xls"],
            accept_multiple_files=True,
            key="uploader_principal",
            label_visibility="collapsed",
        )
        st.button("📤 Carregar Arquivos", use_container_width=True, key="btn_carregar_label", disabled=True)

    with col_b3:
        if st.button("📚 Ler Arquivos", use_container_width=True, key="btn_ler"):
            arquivos_up = st.session_state.get("uploader_principal", []) or []
            if not arquivos_up:
                st.warning("Nenhum arquivo carregado ainda. Use o botão ‘Carregar Arquivos’ primeiro.")
            else:
                processados = [_processar_arquivo(f) for f in arquivos_up]
                st.session_state["arquivos_processados"] = processados
                st.session_state["full_content"]         = obter_resumo_arquivos(processados)
                # Registra na memória do runtime
                rt = get_runtime()
                for arq in processados:
                    rt.registrar_arquivo(arq["name"])
                _dialog_leitura_ok([a["name"] for a in processados])

    st.divider()

    if os.path.exists("./src/img/perfil-analista.png"):
        st.sidebar.image("./src/img/perfil-analista.png", width=500)

    if st.sidebar.button("🔄 Limpar Conversa"):
        get_runtime().reset_session()
        st.rerun()

    render_cost_widget()

    if "messages" not in st.session_state:
        nome = st.session_state.get("primeiro_nome", "Usuário")
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": f"🌟 {nome}, estou aqui para te ajudar a analisar documentos. "
                       "Carregue seus arquivos e faça suas perguntas! 💡",
        }]

    for msg in st.session_state["messages"]:
        avatar = obter_avatar_usuario() if msg["role"] == "user" else icons["assistant"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    if prompt := st.chat_input("Digite sua pergunta aqui:", key="chat_input_analista"):
        avatar   = obter_avatar_usuario()
        intencao = verificar_intencao_usuario(prompt)

        with st.chat_message("user", avatar=avatar):
            st.write(prompt)

        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        st.session_state["messages"].append({"role": "user", "content": prompt})

        arquivos_sess  = st.session_state.get("arquivos_processados", [])
        resposta_local = responder_pergunta_simples(prompt, arquivos_sess)
        if resposta_local:
            with st.chat_message("assistant", avatar=icons["assistant"]):
                st.write(resposta_local)
            st.session_state["messages"].append({"role": "assistant", "content": resposta_local})
            return

        if intencao:
            time.sleep(0.5)
            with st.chat_message("assistant", avatar=icons["assistant"]):
                if intencao == "plano":
                    mostrar_formulario_plano()
                else:
                    _agenda.renderizar_formulario()
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

            except Exception as e:
                st.error(f"Erro ao gerar análise: {e}")

    botoes_exportacao()
