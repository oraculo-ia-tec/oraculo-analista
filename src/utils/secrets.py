# ============================================================
# src/utils/secrets.py
# Helper para leitura segura de secrets no Streamlit Cloud
# Suporta tanto st.secrets (Streamlit Cloud) quanto decouple (.env)
# ============================================================
import os
import streamlit as st


def get_secret(key: str, section: str | None = None, default: str = "") -> str:
    """
    Lê um secret com fallback em cascata:
      1. st.secrets[section][key]  — Streamlit Cloud (TOML com seção)
      2. st.secrets[key]           — Streamlit Cloud (TOML sem seção)
      3. os.environ[key]           — variável de ambiente do sistema
      4. default                   — valor padrão
    """
    # 1. st.secrets com seção (ex: [groq] GROQ_API_KEY)
    if section:
        try:
            return st.secrets[section][key]
        except (KeyError, AttributeError, FileNotFoundError):
            pass

    # 2. st.secrets sem seção
    try:
        return st.secrets[key]
    except (KeyError, AttributeError, FileNotFoundError):
        pass

    # 3. variável de ambiente (decouple / .env)
    value = os.environ.get(key, "")
    if value:
        return value

    return default
