# ============================================================
# src/styles/theme.py  —  Oráculo Analista
# Fonte única de identidade visual do sistema.
# Importe apply_global_theme() em qualquer página.
# ============================================================
import streamlit as st

# ── Paleta de cores ─────────────────────────────────────────
COR_PRIMARIA   = "#8A2BE2"   # violeta
COR_SECUNDARIA = "#a084ca"   # lilás
COR_DESTAQUE   = "#e0c3fc"   # lavanda clara
COR_OURO       = "gold"
COR_CREME      = "#f5f5dc"
COR_BG_DARK    = "#0e0e1a"
COR_BG_CARD    = "#1a1a2e"
COR_BG_CARD2   = "#16213e"
COR_TEXTO      = "#ffffff"
COR_SUBTEXTO   = "#b0b8d1"

# ── CSS global ──────────────────────────────────────────────
_CSS_GLOBAL = f"""
<style>
/* ── Reset e fundo ── */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(160deg, {COR_BG_DARK} 0%, #1a1a2e 100%);
}}
[data-testid="stSidebar"] {{
    background: {COR_BG_CARD} !important;
    border-right: 1px solid {COR_SECUNDARIA}33;
}}

/* ── Tipografia ── */
.oa-title {{
    font-size: 3rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, {COR_PRIMARIA}, {COR_TEXTO});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
    line-height: 1.15;
}}
.oa-subtitle {{
    font-size: 1.2rem;
    text-align: center;
    color: {COR_SUBTEXTO};
    margin-bottom: 2rem;
}}
.oa-section {{
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(90deg, {COR_SECUNDARIA}, {COR_DESTAQUE});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}}
.oa-gradient-creme {{
    background: linear-gradient(90deg, {COR_CREME}, {COR_OURO});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
}}
.oa-gradient-ouro {{
    background: linear-gradient(90deg, {COR_OURO}, {COR_CREME});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
}}

/* ── Cards ── */
.oa-card {{
    border: 1.5px solid {COR_SECUNDARIA}55;
    border-radius: 14px;
    padding: 22px 24px;
    background: linear-gradient(135deg, {COR_BG_CARD} 0%, {COR_BG_CARD2} 100%);
    box-shadow: 0 4px 24px 0 {COR_PRIMARIA}22;
    margin-bottom: 16px;
    color: {COR_TEXTO};
}}
.oa-card-icon {{
    font-size: 2rem;
    margin-bottom: 8px;
}}
.oa-card-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: {COR_DESTAQUE};
    margin-bottom: 4px;
}}
.oa-card-body {{
    font-size: 0.92rem;
    color: {COR_SUBTEXTO};
    line-height: 1.55;
}}

/* ── Métricas hero ── */
.oa-metric {{
    text-align: center;
    padding: 16px 8px;
    border-radius: 12px;
    background: {COR_BG_CARD};
    border: 1px solid {COR_SECUNDARIA}44;
}}
.oa-metric-valor {{
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, {COR_SECUNDARIA}, {COR_DESTAQUE});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.oa-metric-label {{
    font-size: 0.82rem;
    color: {COR_SUBTEXTO};
    margin-top: 2px;
}}

/* ── Divider ── */
.oa-divider {{
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, {COR_SECUNDARIA}88, transparent);
    margin: 2rem 0;
}}

/* ── Chat customização ── */
[data-testid="stChatMessage"] {{
    border-radius: 12px;
    margin-bottom: 8px;
}}
.stChatInputContainer {{
    border-top: 1px solid {COR_SECUNDARIA}44 !important;
}}

/* ── Botão primário ── */
.stButton > button {{
    background: linear-gradient(90deg, {COR_PRIMARIA}, {COR_SECUNDARIA}) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s;
}}
.stButton > button:hover {{
    opacity: 0.88;
}}
</style>
"""


def apply_global_theme() -> None:
    """Injeta o CSS global do Oráculo Analista na página atual."""
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


def card(icon: str, titulo: str, corpo: str) -> str:
    """Retorna HTML de um card padronizado."""
    return f"""
    <div class="oa-card">
      <div class="oa-card-icon">{icon}</div>
      <div class="oa-card-title">{titulo}</div>
      <div class="oa-card-body">{corpo}</div>
    </div>
    """


def metrica(valor: str, label: str) -> str:
    """Retorna HTML de uma métrica hero."""
    return f"""
    <div class="oa-metric">
      <div class="oa-metric-valor">{valor}</div>
      <div class="oa-metric-label">{label}</div>
    </div>
    """


def divider() -> None:
    """Renderiza um divisor gradiente."""
    st.markdown('<hr class="oa-divider">', unsafe_allow_html=True)


def titulo(texto: str) -> None:
    st.markdown(f'<div class="oa-title">{texto}</div>', unsafe_allow_html=True)


def subtitulo(texto: str) -> None:
    st.markdown(f'<div class="oa-subtitle">{texto}</div>', unsafe_allow_html=True)


def section_header(texto: str) -> None:
    st.markdown(f'<div class="oa-section">{texto}</div>', unsafe_allow_html=True)
