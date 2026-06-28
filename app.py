# ============================================================
# app.py — Oráculo Analista
# Router principal — orquestra páginas e sessão
# ============================================================
import os
import streamlit as st

from src.models.base import Base, engine
from src.auth.ui import interface
from src.styles.theme import apply_global_theme
from src.admin.access import tem_acesso_admin
from analista import oraculo_analista
from notification import Notificador  # noqa: F401 — garante import no deploy

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

    # Monta menu dinamicamente conforme cargo
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
        import home  # noqa — aciona landing page
        return

    user = st.session_state.user

    # Atualiza primeiro nome
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
