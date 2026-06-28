# ============================================================
# api_asaas.py — Oráculo Analista
# Entry point do servidor FastAPI (webhook Asaas)
# Rodar: uvicorn api_asaas:app --host 0.0.0.0 --port 8000
# ============================================================
from src.payments.webhook import app  # noqa: F401 — re-exporta a app FastAPI
