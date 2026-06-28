# ============================================================
# tests/conftest.py — fixtures globais compartilhadas
# ============================================================
import pytest


@pytest.fixture
def mock_secrets(monkeypatch):
    """Simula st.secrets sem precisar do Streamlit rodando."""
    import streamlit as st

    class _Secrets(dict):
        def __getattr__(self, item):
            return self[item]

    secrets = _Secrets({
        "groq":    {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "llama-3.3-70b-versatile"},
        "default": {"DATABASE_URL": "sqlite:///:memory:", "APP_BASE_URL": "http://localhost"},
        "email":   {
            "EMAIL_HOST": "smtp.test.com", "EMAIL_PORT": 465,
            "EMAIL_USERNAME": "test@test.com", "EMAIL_PASSWORD": "senha",
            "EMAIL_USE_TLS": False, "EMAIL_USE_SSL": True,
            "EMAIL_REMETENTE": "test@test.com",
        },
    })
    monkeypatch.setattr(st, "secrets", secrets)
    return secrets


@pytest.fixture
def mock_session_state(monkeypatch):
    """Simula st.session_state como dicionário simples."""
    import streamlit as st

    state = {}

    class _State(dict):
        def __getattr__(self, key):
            return self.get(key)

        def __setattr__(self, key, val):
            self[key] = val

    s = _State()
    monkeypatch.setattr(st, "session_state", s)
    return s
