# ============================================================
# app.py — Oráculo Analista
# Router principal — set_page_config DEVE ser o primeiro comando
# ============================================================
import os
import streamlit as st

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.models.base import Base, engine          # noqa: E402
from src.models.migrate import rodar_migrations   # noqa: E402
from src.auth.ui import interface                  # noqa: E402
from src.styles.theme import apply_global_theme    # noqa: E402
from src.admin.access import tem_acesso_admin      # noqa: E402
from src.sidebar import render_configuracao, render_usuarios, tem_acesso_usuarios  # noqa: E402
from analista import oraculo_analista              # noqa: E402
from pagamentos import render_painel_pagamentos    # noqa: E402
from notification import Notificador               # noqa: E402

# 1º cria tabelas novas
Base.metadata.create_all(engine)
# 2º adiciona colunas que não existiam no banco já criado
rodar_migrations()

apply_global_theme()


def _sidebar_usuario_logado(user) -> str:
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

    paginas = ["🤖 Oráculo Analista", "⚙️ Configuração"]
    if tem_acesso_admin(user):
        paginas.append("📊 Dashboard Admin")
        paginas.append("💰 Financeiro")
    if tem_acesso_usuarios(user):
        paginas.append("👥 Usuários")

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
    elif pagina == "⚙️ Configuração":
        render_configuracao()
    elif pagina == "👥 Usuários":
        render_usuarios()
    elif pagina == "💰 Financeiro":
        render_painel_pagamentos()
    else:
        oraculo_analista()


if __name__ == "__main__":
    main()
