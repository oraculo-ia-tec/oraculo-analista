# ============================================================
# src/payments/service.py
# AsaasService — cliente HTTP para a API Asaas
# ============================================================
from __future__ import annotations

import logging

import requests
import streamlit as st

from ..models.base import Session
from ..models.user import UserAnalise
from .plans import PLANOS, calcular_vencimento

logger = logging.getLogger("asaas_service")

_STATUS_PT = {
    "PENDING":   "Pendente",
    "RECEIVED":  "Recebido",
    "CONFIRMED": "Confirmado",
    "OVERDUE":   "Vencido",
    "REFUNDED":  "Estornado",
    "CANCELLED": "Cancelado",
}


class AsaasService:
    def __init__(self):
        try:
            self._api_key  = st.secrets["asaas"]["ASAAS_API_KEY"]
            self._base_url = st.secrets.get("asaas", {}).get(
                "BASE_URL_ASAAS", "https://api-sandbox.asaas.com/v3"
            )
        except Exception:
            self._api_key  = ""
            self._base_url = "https://api-sandbox.asaas.com/v3"

        self._headers = {
            "Content-Type": "application/json",
            "access_token": self._api_key,
        }

    def criar_cliente(self, nome: str, email: str, telefone: str) -> dict:
        return self._post("/customers", {"name": nome, "email": email, "mobilePhone": telefone})

    def buscar_cliente(self, customer_id: str) -> dict:
        return self._get(f"/customers/{customer_id}")

    def criar_cobranca_pix(self, cliente_id: str, plano: str, vencimento_dias: int = 3) -> dict:
        import datetime
        info = PLANOS.get(plano, {})
        venc = (datetime.date.today() + datetime.timedelta(days=vencimento_dias)).isoformat()
        return self._post("/payments", {
            "customer":    cliente_id,
            "billingType": "PIX",
            "value":       info.get("preco", 49.90),
            "dueDate":     venc,
            "description": info.get("descricao", "Oráculo Analista"),
        })

    def verificar_pagamento(self, payment_id: str) -> dict:
        return self._get(f"/payments/{payment_id}")

    def listar_pagamentos(self, status: str | None = None) -> list[dict]:
        params = {"status": status} if status else {}
        return self._get("/payments", params=params).get("data", [])

    def ativar_plano(self, email: str, plano: str) -> bool:
        """Ativa o plano do usuário após pagamento confirmado."""
        with Session() as session:
            try:
                user = session.query(UserAnalise).filter_by(email=email).first()
                if not user:
                    return False
                user.pagamento_confirmado = True
                user.acesso_autorizado    = True
                user.plano                = plano
                user.data_vencimento      = calcular_vencimento(plano)
                user.upgrade_solicitado   = None
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Erro ao ativar plano: {e}")
                return False

    @staticmethod
    def status_pt(status_en: str) -> str:
        return _STATUS_PT.get(str(status_en).upper(), status_en)

    def _post(self, path: str, payload: dict) -> dict:
        r = requests.post(self._base_url + path, json=payload, headers=self._headers, timeout=20)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = requests.get(self._base_url + path, headers=self._headers, params=params or {}, timeout=20)
        r.raise_for_status()
        return r.json()
