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


def _avatar_b64(user) -> str:
    """Retorna Base64 da imagem do usuário (banco > arquivo > padrão)."""
    avatar = get_avatar(user)
    if isinstance(avatar, bytes):
        return base64.b64encode(avatar).decode()
    path = str(avatar)
    if os.path.exists(path):
        return _img_to_b64(path)
    fallback = "./src/img/usuario.jpg"
    if os.path.exists(fallback):
        return _img_to_b64(fallback)
    return ""


def _sidebar_logo() -> None:
    """Imagem do Oráculo no topo da sidebar — borda redonda dourada."""
    if not os.path.exists(ORACULO_IMG):
        return
    b64 = _img_to_b64(ORACULO_IMG)
    st.sidebar.markdown(
        f"""
        <div style="display:flex; justify-content:center; padding:10px 0 2px 0;">
            <img src="data:image/png;base64,{b64}"
                 style="width:110px; height:110px;
                        border-radius:50%; object-fit:cover;
                        border:3px solid #c9a84c;
                        box-shadow:0 0 14px rgba(201,168,76,0.55);" />
        </div>
        <div style="text-align:center; font-size:0.8rem; font-weight:700;
                    color:#c9a84c; letter-spacing:2px; margin-bottom:10px;">
            ORÁCULO ANALISTA
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sidebar_user_card(user) -> None:
    """Card retangular: avatar (col esq) + dados (col dir) com borda."""
    av_b64 = _avatar_b64(user)
    img_tag = (
        f'<img src="data:image/png;base64,{av_b64}"'
        ' style="width:64px;height:64px;border-radius:50%;'
        'object-fit:cover;border:2px solid #c9a84c;"/>'
        if av_b64 else
        '<div style="width:64px;height:64px;border-radius:50%;'
        'background:#444;border:2px solid #c9a84c;"></div>'
    )

    plano  = getattr(user, "plano", "free") or "free"
    acesso = getattr(user, "acesso_autorizado", False)
    badge_cor   = "#22c55e" if acesso else "#f59e0b"
    badge_texto = "Ativo" if acesso else "Pendente"

    st.sidebar.markdown(
        f"""
        <div style="
            display:flex; align-items:center; gap:12px;
            border:1px solid #3a3a3a; border-radius:10px;
            padding:10px 12px; margin-bottom:10px;
            background:rgba(255,255,255,0.03);
        ">
            <!-- coluna esquerda: avatar -->
            <div style="flex-shrink:0;">
                {img_tag}
            </div>
            <!-- coluna direita: dados -->
            <div style="flex:1; min-width:0; font-size:0.82rem; line-height:1.55;">
                <div style="font-weight:700; font-size:0.92rem;
                            white-space:nowrap; overflow:hidden;
                            text-overflow:ellipsis;">
                    {user.name}
                </div>
                <div style="color:#aaa; white-space:nowrap; overflow:hidden;
                            text-overflow:ellipsis;">
                    📧 {user.email}
                </div>
                <div style="color:#aaa;">
                    📱 {user.whatsapp}
                </div>
                <div style="margin-top:4px;">
                    <span style="background:#1e1e2e; border:1px solid #555;
                                 border-radius:4px; padding:1px 6px;
                                 font-size:0.75rem; color:#c9a84c;">
                        {plano.capitalize()}
                    </span>
                    <span style="margin-left:6px; background:{badge_cor}22;
                                 border:1px solid {badge_cor};
                                 border-radius:4px; padding:1px 6px;
                                 font-size:0.75rem; color:{badge_cor};">
                        {badge_texto}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sidebar_usuario_logado(user) -> str:
    _sidebar_logo()
    _sidebar_user_card(user)

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
