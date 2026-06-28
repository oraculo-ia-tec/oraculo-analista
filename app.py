# ============================================================
# app.py — Oráculo Analista
# Router principal — orquestra páginas e sessão
# st.set_page_config() DEVE ser a primeira chamada Streamlit
# ============================================================
import os
import streamlit as st

# ⚠️ set_page_config precisa ser a PRIMEIRA chamada — antes de qualquer import de página
st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports após set_page_config
from src.models.base import Base, engine          # noqa: E402
from src.auth.ui import interface                  # noqa: E402
from src.styles.theme import apply_global_theme    # noqa: E402
from src.admin.access import tem_acesso_admin      # noqa: E402
from analista import oraculo_analista              # noqa: E402
from notification import Notificador               # noqa: E402  garante import no deploy

Base.metadata.create_all(engine)
apply_global_theme()


def _sidebar_usuario_logado(user) -> str:
    """Renderiza o sidebar do usuário logado. Retorna a página selecionada."""
    st.sidebar.subheader(f"Bem-vindo(a), {user.name}")

    avatar = (
        user.profile_image_path
        if getattr(user, "profile_image_path", None)
        and os.path.exists(user.profile_image_path or "")
        else "./src/img/usuario.jpg"
    )
    if os.path.exists(avatar):
        st.sidebar.image(avatar, width=100)

    st.sidebar.write(f"📧 {user.email}")
    st.sidebar.write(f"📱 {user.whatsapp}")
    st.sidebar.divider()

    paginas = ["🤖 Oráculo Analista"]
    if tem_acesso_admin(user):
        paginas.append("📊 Dashboard Admin")

    pagina = st.sidebar.radio("Navegar para:", paginas, key="nav_pagina")

    st.sidebar.divider()
    if st.sidebar.button("🔓 Sair do sistema"):
        for key in ["user", "logged_in", "codigo_confirmado", "temp_email",
                    "primeiro_nome", "messages", "full_content",
                    "arquivos_processados", "nav_pagina"]:
            st.session_state.pop(key, None)
        st.rerun()

    return pagina


def main() -> None:
    if not st.session_state.get("logged_in"):
        interface()
        # Chama render() do home.py — nunca importa como módulo de nível superior
        from home import render as render_home
        render_home()
        return

    user = st.session_state.user

    if getattr(user, "name", None):
        st.session_state["primeiro_nome"] = user.name.strip().split()[0]

    pagina = _sidebar_usuario_logado(user)

    if pagina == "📊 Dashboard Admin":
        from src.admin.dashboard import render_dashboard
        render_dashboard()
    else:
        oraculo_analista()


if __name__ == "__main__":
    main()
