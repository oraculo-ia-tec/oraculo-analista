"""
Oráculo Analista — Streamlit App v2.0

Interface principal do produto.
Arquitetura: Runtime (singleton por sessão) → QueryEngine → Tools → LLM

Fluxo de dados:
  1. Usuário faz login → Runtime instanciado e salvo em st.session_state
  2. Usuário faz upload → runtime.load_document()
  3. Usuário digita pergunta → runtime.process_stream() com st.write_stream()
  4. Sidebar exibe métricas em tempo real (tokens, custo, tool calls)
  5. Ao fechar → runtime.close() salva sessão e memória
"""
import os
import tempfile
import atexit

import streamlit as st

from src.runtime import Runtime
from src.utils.helpers import generate_id

# ─── Configuração da página ────────────────────────────────────────────────────

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS customizado ────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Chat input fixo no rodapé */
.stChatInput { position: sticky; bottom: 0; background: #0e1117; padding: 8px 0; z-index: 100; }

/* Badge de documento ativo */
.doc-badge {
    background: #1e3a5f; color: #90caf9; padding: 4px 10px;
    border-radius: 20px; font-size: 12px; font-weight: 600;
    display: inline-block; margin-top: 4px;
}

/* Métrica de custo */
.cost-display {
    background: #1a2e1a; color: #81c784; padding: 6px 12px;
    border-radius: 8px; font-size: 13px; text-align: center;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─── Inicialização do estado ───────────────────────────────────────────────────

def init_session_state():
    """Inicializa todas as chaves do st.session_state."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_name": "",
        "user_email": "",
        "user_plan": "free",
        "runtime": None,
        "messages": [],
        "show_metrics": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ─── Tela de Login ─────────────────────────────────────────────────────────────

def render_login():
    """Tela de login simples. Em produção: integrar com Supabase Auth."""
    st.title("🔮 Oráculo Analista")
    st.markdown("**Análise inteligente de documentos com IA**")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Entrar")
        name = st.text_input("Seu nome", placeholder="João Silva")
        email = st.text_input("E-mail", placeholder="joao@empresa.com")
        plan = st.selectbox(
            "Plano",
            ["free", "pro", "enterprise"],
            format_func=lambda x: {
                "free": "🆓 Gratuito",
                "pro": "⭐ Pro",
                "enterprise": "🏢 Enterprise",
            }[x],
        )

        if st.button("Entrar", type="primary", use_container_width=True):
            if not name or not email:
                st.error("Preencha nome e e-mail.")
                return

            user_id = generate_id(email)
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_name = name
            st.session_state.user_email = email
            st.session_state.user_plan = plan

            # Instancia o Runtime (coração do sistema)
            runtime = Runtime(
                user_id=user_id,
                user_name=name,
                user_email=email,
                user_plan=plan,
            )
            st.session_state.runtime = runtime
            atexit.register(runtime.close)

            # Mensagem de boas-vindas
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    f"Olá, **{name}**! 👋 Sou o Oráculo Analista.\n\n"
                    f"Posso analisar documentos PDF, planilhas Excel e arquivos CSV. "
                    f"Faça o upload de um arquivo no painel à esquerda para começar, "
                    f"ou simplesmente me faça uma pergunta!"
                ),
            })
            st.rerun()

# ─── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(runtime: Runtime):
    """Sidebar com upload, métricas e configurações."""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        plan_labels = {
            "free": "🆓 Gratuito",
            "pro": "⭐ Pro",
            "enterprise": "🏢 Enterprise",
        }
        st.caption(plan_labels.get(st.session_state.user_plan, ""))
        st.divider()

        # Upload de documento
        st.markdown("#### 📎 Documento")
        uploaded = st.file_uploader(
            "Carregar arquivo",
            type=["pdf", "xlsx", "xls", "csv", "txt", "md"],
            label_visibility="collapsed",
        )

        if uploaded:
            suffix = "." + uploaded.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            with st.spinner(f"Carregando {uploaded.name}..."):
                msg = runtime.load_document(filepath=tmp_path, filename=uploaded.name)

            os.unlink(tmp_path)

            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.rerun()

        # Documento ativo
        if runtime.active_document:
            st.markdown(
                f'<div class="doc-badge">📄 {runtime.active_document}</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Métricas da sessão
        st.markdown("#### 📊 Sessão")
        metrics = runtime.get_metrics()

        col1, col2 = st.columns(2)
        col1.metric("Mensagens", metrics["messages"])
        col2.metric("Tool Calls", metrics["tool_calls"])
        st.metric("Tokens usados", f"{metrics['tokens']:,}")

        cost_brl = metrics["cost_brl"]
        st.markdown(
            f'<div class="cost-display">💰 Custo estimado: R$ {cost_brl:.4f}</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # Ações
        col1, col2 = st.columns(2)
        if col1.button("🗑️ Limpar", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        if col2.button("🚪 Sair", use_container_width=True):
            runtime.close()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ─── Chat principal ────────────────────────────────────────────────────────────

def render_chat(runtime: Runtime):
    """Área principal de chat com streaming."""
    st.title("🔮 Oráculo Analista")

    # Exibe histórico de mensagens
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🔮" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Input do usuário
    user_input = st.chat_input(
        "Faça uma pergunta sobre seu documento ou qualquer análise...",
        key="chat_input",
    )

    if user_input:
        # Exibe mensagem do usuário imediatamente
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Streaming da resposta do assistente
        with st.chat_message("assistant", avatar="🔮"):
            response_placeholder = st.empty()
            full_response = ""

            with st.spinner(""):
                for chunk in runtime.process_stream(user_input):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
        })

        st.rerun()

# ─── Entrada principal ─────────────────────────────────────────────────────────

def main():
    if not st.session_state.authenticated:
        render_login()
        return

    runtime: Runtime = st.session_state.runtime
    render_sidebar(runtime)
    render_chat(runtime)


if __name__ == "__main__":
    main()
