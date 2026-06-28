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

import base64
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

ORACULO_IMG = "./src/img/perfil-analista.png"


def _img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _sidebar_logo() -> None:
    """Exibe a imagem do Oráculo no topo da sidebar com borda redonda via HTML."""
    if not os.path.exists(ORACULO_IMG):
        return
    b64 = _img_to_b64(ORACULO_IMG)
    st.sidebar.markdown(
        f"""
        <div style="display:flex; justify-content:center; padding: 8px 0 4px 0;">
            <img src="data:image/png;base64,{b64}"
                 style="width:110px; height:110px;
                        border-radius:50%;
                        object-fit:cover;
                        border: 3px solid #c9a84c;
                        box-shadow: 0 0 12px rgba(201,168,76,0.5);" />
        </div>
        <div style="text-align:center; font-size:0.85rem;
                    color:#c9a84c; letter-spacing:1px;
                    margin-bottom:8px;">
            ORÁCULO ANALISTA
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sidebar_usuario_logado(user) -> str:
    _sidebar_logo()

    # Avatar do usuário com borda redonda
    avatar = get_avatar(user)
    if isinstance(avatar, bytes):
        avatar_b64 = base64.b64encode(avatar).decode()
        st.sidebar.markdown(
            f"""
            <div style="display:flex; flex-direction:column;
                        align-items:center; margin-bottom:6px;">
                <img src="data:image/png;base64,{avatar_b64}"
                     style="width:72px; height:72px;
                            border-radius:50%; object-fit:cover;
                            border:2px solid #888;" />
                <span style="font-size:0.9rem; margin-top:4px;
                             font-weight:600;">{user.name}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # arquivo local ou padrão
        if os.path.exists(str(avatar)):
            av_b64 = _img_to_b64(str(avatar))
            st.sidebar.markdown(
                f"""
                <div style="display:flex; flex-direction:column;
                            align-items:center; margin-bottom:6px;">
                    <img src="data:image/png;base64,{av_b64}"
                         style="width:72px; height:72px;
                                border-radius:50%; object-fit:cover;
                                border:2px solid #888;" />
                    <span style="font-size:0.9rem; margin-top:4px;
                                 font-weight:600;">{user.name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.subheader(user.name)

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
        _sidebar_logo()
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
