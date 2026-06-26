"""
ORÁCULO ANALISTA — CSS Global e Utilitários
Injetado UMA VEZ na inicialização do app via inject_global_styles().
"""
import streamlit as st


_CSS = """
/* ═══════════════════════════════════════════════════════════
   ORÁCULO ANALISTA — Design System CSS v2.0
   ═══════════════════════════════════════════════════════════ */

/* ── Tipografia & Base ──────────────────────────────────── */
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&display=swap');

:root {
  --font-display: 'Cinzel', Georgia, serif;
  --font-body:    'Satoshi', 'Inter', sans-serif;

  --bg:           #0D0D0F;
  --surface:      #141417;
  --surface-2:    #1A1A1F;
  --surface-3:    #1F1F26;
  --border:       #2A2A35;
  --border-sub:   #1E1E28;

  --text:         #E8E6E1;
  --text-muted:   #9896A0;
  --text-faint:   #55545C;

  --gold:         #C9A84C;
  --gold-hover:   #DFC06A;
  --gold-dim:     #3A2F10;
  --gold-glow:    rgba(201,168,76,0.18);

  --violet:       #7C3AED;
  --violet-dim:   #2D1A5A;

  --success:      #3EAF7C;
  --warning:      #E09A3A;
  --error:        #E05252;
  --info:         #3A9BE0;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  --transition: 180ms cubic-bezier(0.16,1,0.3,1);
}

/* ── Superfície principal ────────────────────────────────── */
.stApp {
  background: var(--bg) !important;
  font-family: var(--font-body) !important;
  color: var(--text) !important;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

/* ── Título principal com glow dourado ───────────────────── */
.oa-hero-title {
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 3vw, 2.6rem);
  font-weight: 700;
  background: linear-gradient(110deg, #C9A84C 0%, #F5E27A 40%, #C9A84C 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.04em;
  line-height: 1.2;
  margin: 0 0 4px 0;
}
.oa-hero-subtitle {
  font-size: 0.95rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0 0 24px 0;
}

/* ── Cards / Painéis ─────────────────────────────────────── */
.oa-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.oa-card:hover {
  border-color: var(--gold-dim);
  box-shadow: 0 0 0 1px var(--gold-dim), 0 4px 24px rgba(201,168,76,0.06);
}
.oa-card-title {
  font-family: var(--font-display);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gold);
  margin: 0 0 12px 0;
}

/* ── Divisor com acento ──────────────────────────────────── */
.oa-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  border: none;
  margin: 24px 0;
}
.oa-divider-gold {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  border: none;
  margin: 24px 0;
}

/* ── Badges de status ────────────────────────────────────── */
.oa-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.03em;
}
.oa-badge-gold    { background: var(--gold-dim);          color: var(--gold);    border: 1px solid rgba(201,168,76,0.3); }
.oa-badge-success { background: rgba(62,175,124,0.12);    color: var(--success); border: 1px solid rgba(62,175,124,0.25); }
.oa-badge-warning { background: rgba(224,154,58,0.12);    color: var(--warning); border: 1px solid rgba(224,154,58,0.25); }
.oa-badge-error   { background: rgba(224,82,82,0.12);     color: var(--error);   border: 1px solid rgba(224,82,82,0.25); }
.oa-badge-info    { background: rgba(58,155,224,0.12);    color: var(--info);    border: 1px solid rgba(58,155,224,0.25); }

/* ── Botões primários Streamlit ──────────────────────────── */
.stButton > button[kind="primary"],
.stButton > button {
  background: transparent !important;
  color: var(--gold) !important;
  border: 1px solid var(--gold) !important;
  border-radius: var(--radius-md) !important;
  font-family: var(--font-body) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  padding: 8px 18px !important;
  transition: all var(--transition) !important;
  box-shadow: none !important;
}
.stButton > button:hover {
  background: var(--gold-dim) !important;
  border-color: var(--gold-hover) !important;
  color: var(--gold-hover) !important;
  box-shadow: 0 0 12px var(--gold-glow) !important;
}
.stButton > button:active {
  transform: scale(0.98) !important;
}

/* ── File uploader ───────────────────────────────────────── */
.stFileUploader > div {
  background: var(--surface-2) !important;
  border: 1px dashed var(--border) !important;
  border-radius: var(--radius-lg) !important;
  transition: border-color var(--transition) !important;
}
.stFileUploader > div:hover {
  border-color: var(--gold) !important;
}

/* ── Inputs e selects ────────────────────────────────────── */
.stTextInput input, .stTextArea textarea,
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text) !important;
  font-family: var(--font-body) !important;
  transition: border-color var(--transition) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px var(--gold-dim) !important;
  outline: none !important;
}

/* ── Chat messages ───────────────────────────────────────── */
div[data-testid="stChatMessage"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border-sub) !important;
  border-radius: var(--radius-lg) !important;
  margin-bottom: 8px !important;
}

/* ── Chat input ──────────────────────────────────────────── */
div[data-testid="stChatInputContainer"] {
  background: var(--surface) !important;
  border-top: 1px solid var(--border) !important;
}
div[data-testid="stChatInputContainer"] textarea {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text) !important;
}

/* ── Download buttons ────────────────────────────────────── */
.stDownloadButton > button {
  background: var(--surface-3) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-muted) !important;
  border-radius: var(--radius-md) !important;
  font-size: 0.8rem !important;
  transition: all var(--transition) !important;
}
.stDownloadButton > button:hover {
  border-color: var(--gold) !important;
  color: var(--gold) !important;
}

/* ── Spinner ─────────────────────────────────────────────── */
.stSpinner > div {
  border-top-color: var(--gold) !important;
}

/* ── Métricas ────────────────────────────────────────────── */
div[data-testid="metric-container"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 16px !important;
}
div[data-testid="metric-container"] label {
  color: var(--text-muted) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Alertas nativos ─────────────────────────────────────── */
div[data-testid="stAlert"] {
  border-radius: var(--radius-md) !important;
  border-left-width: 3px !important;
}

/* ── Scrollbar customizada ───────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }

/* ── Selection ───────────────────────────────────────────── */
::selection { background: var(--gold-dim); color: var(--gold-hover); }

/* ── Compatibilidade com classes legadas de landing ──────── */
.titulo-principal, .title {
  font-family: var(--font-display) !important;
  background: linear-gradient(110deg, #C9A84C, #F5E27A, #C9A84C) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-weight: 700 !important;
  text-align: center;
}
.subtitulo, .subtitle, .section-header {
  font-family: var(--font-display) !important;
  color: var(--gold) !important;
  -webkit-text-fill-color: var(--gold) !important;
}
.descricao-gradient, .benefit-item {
  color: var(--text-muted) !important;
  -webkit-text-fill-color: var(--text-muted) !important;
  background: none !important;
}

/* ── Sidebar brand ───────────────────────────────────────── */
.oa-sidebar-brand {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  background: linear-gradient(110deg, #C9A84C, #F5E27A);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.06em;
  padding: 8px 0 16px;
  display: block;
  text-align: center;
}

/* ── Section header ──────────────────────────────────────── */
.oa-section-header {
  font-family: var(--font-display);
  font-size: 0.8rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--gold);
  margin: 24px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--gold-dim);
}

/* ── Empty state ─────────────────────────────────────────── */
.oa-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  color: var(--text-faint);
}
.oa-empty-state h4 {
  color: var(--text-muted);
  font-family: var(--font-body);
  font-size: 1rem;
  margin: 12px 0 6px;
}
.oa-empty-state p {
  font-size: 0.875rem;
  max-width: 36ch;
  margin: 0;
}

/* ── Footer ──────────────────────────────────────────────── */
.oa-footer {
  text-align: center;
  color: var(--text-faint);
  font-size: 0.75rem;
  padding: 24px 0 8px;
  letter-spacing: 0.04em;
}
.oa-footer span {
  color: var(--gold);
}
"""


def inject_global_styles() -> None:
    """Injeta o CSS global do Design System. Chamar UMA vez no início do app."""
    st.html(f"<style>{_CSS}</style>")
