"""
ORÁCULO ANALISTA — Componentes Reutilizáveis
Todos os wrappers visuais do app. Importe daqui — nunca repita HTML/CSS inline.
Lógica Python, callbacks e session_state permanecem nos módulos de negócio.
"""
import streamlit as st


# ══════════════════════════════════════════════════════════════
#  TIPOGRAFIA / CABEÇALHOS
# ══════════════════════════════════════════════════════════════

def hero_header(title: str = "Oráculo Analista", subtitle: str = "") -> None:
    """Cabeçalho principal com título em fonte display dourada e subtítulo muted."""
    sub_html = f'<p class="oa-hero-subtitle">{subtitle}</p>' if subtitle else ""
    st.html(f"""
        <div style="padding: 8px 0 4px;">
            <h1 class="oa-hero-title">{title}</h1>
            {sub_html}
        </div>
    """)


def section_header(label: str) -> None:
    """Header de seção com linha dourada inferior. Substitui st.subheader."""
    st.html(f'<div class="oa-section-header">{label}</div>')


def sidebar_brand(name: str = "⬡ ORÁCULO ANALISTA") -> None:
    """Logo/marca na sidebar."""
    st.sidebar.markdown(
        f'<span class="oa-sidebar-brand">{name}</span>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
#  CARDS / PAINÉIS
# ══════════════════════════════════════════════════════════════

def card(title: str = "", content_html: str = "", key: str = "") -> None:
    """Painel com borda escura e hover dourado. Só para conteúdo estático."""
    title_html = f'<div class="oa-card-title">{title}</div>' if title else ""
    st.html(f'''
        <div class="oa-card" id="card-{key}">
            {title_html}
            {content_html}
        </div>
    ''')


def feature_card(icon: str, title: str, description: str) -> None:
    """Card de feature para landing page."""
    st.html(f"""
        <div class="oa-card" style="height:100%;">
            <div style="font-size:1.5rem; margin-bottom:8px;">{icon}</div>
            <div class="oa-card-title">{title}</div>
            <p style="color:var(--text-muted); font-size:0.875rem; line-height:1.6; margin:0;">{description}</p>
        </div>
    """)


# ══════════════════════════════════════════════════════════════
#  DIVISORES
# ══════════════════════════════════════════════════════════════

def divider(gold: bool = False) -> None:
    """Divisor sutil. gold=True usa acento dourado."""
    cls = "oa-divider-gold" if gold else "oa-divider"
    st.html(f'<hr class="{cls}">')


# ══════════════════════════════════════════════════════════════
#  BADGES DE STATUS
# ══════════════════════════════════════════════════════════════

_BADGE_MAP = {
    "gold":    "oa-badge-gold",
    "success": "oa-badge-success",
    "warning": "oa-badge-warning",
    "error":   "oa-badge-error",
    "info":    "oa-badge-info",
}


def status_badge(label: str, kind: str = "gold", dot: bool = True) -> str:
    """Retorna HTML de badge. Use com st.html() ou embutido em outros componentes."""
    cls  = _BADGE_MAP.get(kind, "oa-badge-gold")
    _dot = '<span style="font-size:0.55rem;">●</span>' if dot else ""
    return f'<span class="oa-badge {cls}">{_dot} {label}</span>'


def render_badge(label: str, kind: str = "gold") -> None:
    """Renderiza badge inline."""
    st.html(status_badge(label, kind))


# ══════════════════════════════════════════════════════════════
#  ESTADOS ESPECIAIS
# ══════════════════════════════════════════════════════════════

def empty_state(
    title: str = "Nada por aqui ainda",
    description: str = "Envie seus arquivos e comece a análise.",
    icon: str = "🔮",
) -> None:
    """Estado vazio com ícone, título e descrição."""
    st.html(f"""
        <div class="oa-empty-state">
            <div style="font-size:2.5rem; opacity:0.5;">{icon}</div>
            <h4>{title}</h4>
            <p>{description}</p>
        </div>
    """)


# ══════════════════════════════════════════════════════════════
#  PAINÉIS COMPOSTOS
# ══════════════════════════════════════════════════════════════

def upload_panel(
    label: str = "Envie seus documentos",
    description: str = "PDF, Excel, Word, JSON, XML, HTML, TXT",
    accepted_types: list | None = None,
    multiple: bool = True,
    key: str = "upload",
):
    """
    Painel de upload padronizado com título e instrução.
    Retorna o objeto de arquivos do st.file_uploader.
    """
    accepted = accepted_types or ["xlsx", "pdf", "xml", "json", "html", "htm", "doc", "docx", "txt", "xls"]
    section_header(label)
    st.caption(description)
    return st.file_uploader(
        label="",
        type=accepted,
        accept_multiple_files=multiple,
        key=key,
        label_visibility="collapsed",
    )


def user_profile_block(name: str, email: str, whatsapp: str, image_path: str | None = None) -> None:
    """Bloco de perfil do usuário na sidebar."""
    if image_path:
        try:
            st.sidebar.image(image_path, width=72)
        except Exception:
            pass
    st.sidebar.html(f"""
        <div style="padding:8px 0 4px;">
            <div style="font-size:0.9rem; font-weight:600; color:#E8E6E1;">{name}</div>
            <div style="font-size:0.75rem; color:#9896A0; margin-top:2px;">{email}</div>
            <div style="font-size:0.75rem; color:#9896A0;">{whatsapp}</div>
        </div>
    """)


def footer(credits: str = "Oráculos IA") -> None:
    """Rodapé padronizado."""
    st.html(f'''
        <div class="oa-footer">
            Desenvolvido com ♥ por <span>{credits}</span>
        </div>
    ''')


# ══════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════

def dialog_info_decorator(title: str, width: str = "small"):
    """
    Decorador para criar dialogs padronizados com st.dialog.

    Uso:
        @dialog_info_decorator("Título do Dialog")
        def meu_dialog():
            st.write("Conteúdo...")

        if st.button("Abrir"):
            meu_dialog()
    """
    def decorator(func):
        @st.dialog(title, width=width)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════
#  LANDING PAGE HELPERS
# ══════════════════════════════════════════════════════════════

def landing_feature_grid(features: list[dict]) -> None:
    """
    Renderiza grid de features para landing page.
    features: lista de dicts com chaves: icon, title, description
    """
    for i in range(0, len(features), 2):
        row = features[i:i+2]
        cols = st.columns(len(row), gap="medium")
        for col, feat in zip(cols, row):
            with col:
                feature_card(feat["icon"], feat["title"], feat["description"])
        st.write("")


def landing_cta_button(label: str = "Comece Agora →", key: str = "cta") -> bool:
    """Botão de CTA centralizado para landing page. Retorna True se clicado."""
    col = st.columns([1, 2, 1])[1]
    with col:
        return st.button(label, key=key, use_container_width=True)
