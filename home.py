# ============================================================
# home.py  —  Oráculo Analista
# Landing page refatorada com theme centralizado.
# ============================================================
import os
import streamlit as st
from src.styles.theme import (
    apply_global_theme, card, metrica, divider,
    titulo, subtitulo, section_header,
)

st.set_page_config(
    page_title="Oráculo Analista",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_theme()

# ── Hero ────────────────────────────────────────────────────
col_img, col_txt = st.columns([1, 2], gap="large")
with col_img:
    if os.path.exists("./src/img/oraculo-analista-home2.png"):
        st.image("./src/img/oraculo-analista-home2.png", use_container_width=True)

with col_txt:
    titulo("Oráculo Analista")
    subtitulo("Transformando documentos complexos em decisões estratégicas com IA")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Começar Agora", use_container_width=True, key="cta_hero"):
        st.switch_page("app.py")

divider()

# ── Métricas ────────────────────────────────────────────────
section_header("Resultados comprovados")
m1, m2, m3, m4 = st.columns(4)
metricas = [
    ("m1", "+300%",  "Produtividade"),
    ("m2", "< 2s",   "Tempo de resposta"),
    ("m3", "50+",    "Formatos suportados"),
    ("m4", "100%",   "Dados seguros"),
]
for col, (_, val, lbl) in zip([m1, m2, m3, m4], metricas):
    with col:
        st.markdown(metrica(val, lbl), unsafe_allow_html=True)

divider()

# ── Vantagens ───────────────────────────────────────────────
section_header("Por que o Oráculo Analista?")
v1, v2, v3 = st.columns(3)
with v1:
    st.markdown(card(
        "⚡", "Agilidade nas Respostas",
        "Processa grandes volumes de dados em tempo real. "
        "Respostas instantâneas para perguntas complexas sobre seus documentos."
    ), unsafe_allow_html=True)
with v2:
    st.markdown(card(
        "🎯", "Precisão nas Análises",
        "IA avançada interpreta dados e minimiza erros humanos. "
        "Resultados consistentes para decisões seguras."
    ), unsafe_allow_html=True)
with v3:
    st.markdown(card(
        "🔒", "Segurança Total",
        "Seus dados nunca saem do ambiente seguro. "
        "Conformidade com boas práticas de privacidade."
    ), unsafe_allow_html=True)

divider()

# ── Benefícios ──────────────────────────────────────────────
section_header("Benefícios para Empresários")
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(card(
        "📈", "Aumento de Faturamento",
        "Identifique oportunidades estratégicas com análise de mercado baseada em dados reais."
    ), unsafe_allow_html=True)
with b2:
    st.markdown(card(
        "💰", "Redução de Custos",
        "Detecte ineficiências operacionais e otimize processos antes que virem prejuízo."
    ), unsafe_allow_html=True)
with b3:
    st.markdown(card(
        "🔮", "Previsibilidade",
        "Projeções baseadas em histórico real para planejamento estratégico de longo prazo."
    ), unsafe_allow_html=True)

divider()

# ── Resultados ──────────────────────────────────────────────
section_header("Resultados Gerados")
r1, r2, r3 = st.columns(3)
with r1:
    st.markdown(card(
        "🧠", "Decisões Baseadas em Dados",
        "Abandone o achismo. Adote uma abordagem orientada por dados para decisões mais eficazes."
    ), unsafe_allow_html=True)
with r2:
    st.markdown(card(
        "⚙️", "Eficiência Operacional",
        "Melhore processos de negócio e reduza tarefas administrativas repetitivas."
    ), unsafe_allow_html=True)
with r3:
    st.markdown(card(
        "🌱", "Crescimento Sustentável",
        "Foco em estratégias de longo prazo para crescimento saudável e consistente."
    ), unsafe_allow_html=True)

divider()

# ── CTA final ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    st.markdown(
        '<div style="text-align:center;color:#b0b8d1;margin-bottom:1rem;">'
        'Junte-se a empresários que já tomam decisões mais rápidas e precisas.</div>',
        unsafe_allow_html=True,
    )
    if st.button("🚀 Começar Agora — Grátis", use_container_width=True, key="cta_bottom"):
        st.switch_page("app.py")

st.markdown(
    "<br><small><center>Desenvolvido com ❤️ por Oráculos AI</center></small>",
    unsafe_allow_html=True,
)
