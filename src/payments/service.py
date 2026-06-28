# ============================================================
# src/payments/service.py
# AsaasService — cliente HTTP para a API Asaas
# Sem dependências de UI — puríssimo Python
# ============================================================
from __future__ import annotations

import datetime
import logging

import requests
import streamlit as st

from ..models.base import Session
from .models import UserAnalisePayment
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
    """
    Encapsula todas as chamadas à API Asaas.
    Instâncie uma vez e reutilize.
    """

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

    # ── clientes ─────────────────────────────────────────
    def criar_cliente(self, nome: str, email: str, telefone: str) -> dict:
        payload = {"name": nome, "email": email, "mobilePhone": telefone}
        return self._post("/customers", payload)

    def buscar_cliente(self, customer_id: str) -> dict:
        return self._get(f"/customers/{customer_id}")

    # ── cobranças ───────────────────────────────────────
    def criar_cobranca_pix(
        self,
        cliente_id: str,
        plano: str,
        vencimento_dias: int = 3,
    ) -> dict:
        info = PLANOS.get(plano, {})
        venc = (datetime.date.today() + datetime.timedelta(days=vencimento_dias)).isoformat()
        payload = {
            "customer":   cliente_id,
            "billingType": "PIX",
            "value":      info.get("preco", 49.90),
            "dueDate":    venc,
            "description": info.get("descricao", "Oráculo Analista"),
        }
        return self._post("/payments", payload)

    def verificar_pagamento(self, payment_id: str) -> dict:
        return self._get(f"/payments/{payment_id}")

    def listar_pagamentos(self, status: str | None = None) -> list[dict]:
        params = {"status": status} if status else {}
        data   = self._get("/payments", params=params)
        return data.get("data", [])

    # ── atualização de plano no banco ─────────────────────
    def ativar_plano(self, email: str, plano: str) -> bool:
        """Ativa o plano do usuário após pagamento confirmado."""
        with Session() as session:
            try:
                user = session.query(UserAnalisePayment).filter_by(email=email).first()
                if not user:
                    logger.warning(f"Usuário não encontrado para ativação: {email}")
                    return False

                user.pagamento_confirmado = True
                user.acesso_autorizado    = True
                user.plano                = plano
                user.data_vencimento      = calcular_vencimento(plano)
                user.upgrade_solicitado   = None
                session.commit()
                logger.info(f"Plano '{plano}' ativado para {email}")
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Erro ao ativar plano: {e}")
                return False

    @staticmethod
    def status_pt(status_en: str) -> str:
        return _STATUS_PT.get(status_en.upper(), status_en)

    # ── HTTP helpers ────────────────────────────────────
    def _post(self, path: str, payload: dict) -> dict:
        url = self._base_url + path
        logger.info(f"POST {url} payload={list(payload.keys())}")
        r = requests.post(url, json=payload, headers=self._headers, timeout=20)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = self._base_url + path
        logger.info(f"GET {url} params={params}")
        r = requests.get(url, headers=self._headers, params=params or {}, timeout=20)
        r.raise_for_status()
        return r.json()
