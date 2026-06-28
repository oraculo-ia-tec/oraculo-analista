import streamlit as st

# ============================================================
# SKILL DE SEGURANÇA — Todas as credenciais via st.secrets
# Configure os valores no painel do Streamlit Cloud:
# App Settings > Secrets
# ============================================================

# --- DATABASE ---
DATABASE_URL = st.secrets["default"]["DATABASE_URL"]
APP_BASE_URL = st.secrets["default"]["APP_BASE_URL"]

# --- GROQ AI ---
GROQ_API_KEY = st.secrets["groq"]["GROQ_API_KEY"]
GROQ_MODEL   = st.secrets["groq"]["GROQ_MODEL"]

# --- EMAIL ---
EMAIL_HOST      = st.secrets["email"]["EMAIL_HOST"]
EMAIL_PORT      = st.secrets["email"]["EMAIL_PORT"]
EMAIL_USERNAME  = st.secrets["email"]["EMAIL_USERNAME"]
EMAIL_PASSWORD  = st.secrets["email"]["EMAIL_PASSWORD"]
EMAIL_USE_TLS   = st.secrets["email"]["EMAIL_USE_TLS"]
EMAIL_USE_SSL   = st.secrets["email"]["EMAIL_USE_SSL"]
EMAIL_REMETENTE = st.secrets["email"]["EMAIL_REMETENTE"]

# --- ASAAS (Pagamentos) ---
# Adicione ao Streamlit Secrets: [asaas] ASAAS_API_KEY = "sua_chave"
ASAAS_API_KEY = st.secrets.get("asaas", {}).get("ASAAS_API_KEY", "")

# --- WEBHOOKS ---
# Adicione ao Streamlit Secrets: [webhooks] WEBHOOK_CADASTRO_ANALISTA = "url"
WEBHOOK_CADASTRO_ANALISTA = st.secrets.get("webhooks", {}).get("WEBHOOK_CADASTRO_ANALISTA", "")
WEBHOOK_TESTE             = st.secrets.get("webhooks", {}).get("WEBHOOK_TESTE", "")

# --- FASTAPI ---
# Adicione ao Streamlit Secrets: [fastapi] FASTAPI_URL = "url"
FASTAPI_URL = st.secrets.get("fastapi", {}).get("FASTAPI_URL", "")
