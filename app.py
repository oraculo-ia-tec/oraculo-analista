# ============================================================
# app.py — Oráculo Analista
# Router principal
# ============================================================
import streamlit as st

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
from src.models.base import Base, engine
from src.models.migrate import rodar_migrations
from src.auth.ui import interface
from src.styles.theme import apply_global_theme
from src.admin.access import tem_acesso_admin
from src.sidebar import render_configuracao, render_usuarios, tem_acesso_usuarios
from src.utils.avatar import get_avatar
from analista import oraculo_analista
from pagamentos import render_painel_pagamentos
from notification import Notificador  # noqa

Base.metadata.create_all(engine)
rodar_migrations()
apply_global_theme()


def _sidebar_usuario_logado(user) -> str:
    st.sidebar.subheader(f"Bem-vindo(a), {user.name}")

    # ── Avatar: Base64 (banco) > arquivo local > padrão ──
    avatar = get_avatar(user)
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
