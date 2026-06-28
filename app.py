# ============================================================
# app.py — Oráculo Analista
# Router principal — apenas orquestra páginas e sessão
# ============================================================
import os
import streamlit as st

from src.models.base import Base, engine
from src.auth.ui import interface
from src.styles.theme import apply_global_theme
from analista import oraculo_analista
from notification import Notificador  # noqa: F401 — garante import no deploy

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cria tabelas se não existirem
Base.metadata.create_all(engine)

apply_global_theme()


def _sidebar_usuario_logado() -> None:
    user = st.session_state.user
    st.sidebar.subheader(f"Bem-vindo(a), {user.name}")

    avatar = (
        user.profile_image_path
        if getattr(user, "profile_image_path", None) and os.path.exists(user.profile_image_path)
        else "./src/img/usuario.jpg"
    )
    if os.path.exists(avatar):
        st.sidebar.image(avatar, width=100)

    st.sidebar.write(f"📧 {user.email}")
    st.sidebar.write(f"📱 {user.whatsapp}")

    if st.sidebar.button("🔓 Sair do sistema"):
        for key in ["user", "logged_in", "codigo_confirmado", "temp_email",
                    "primeiro_nome", "messages", "full_content", "arquivos_processados"]:
            st.session_state.pop(key, None)
        st.rerun()


def main() -> None:
    if not st.session_state.get("logged_in"):
        interface()
        # Landing público enquanto não logado
        from home import __file__ as _  # noqa — aciona home.py via import
        import importlib, sys
        if "home" in sys.modules:
            importlib.reload(sys.modules["home"])
        else:
            import home  # noqa
    else:
        _sidebar_usuario_logado()
        # Atualiza primeiro nome na sessão
        user = st.session_state.user
        if getattr(user, "name", None):
            st.session_state["primeiro_nome"] = user.name.strip().split()[0]
        oraculo_analista()


if __name__ == "__main__":
    main()
