# ============================================================
# src/payments/webhook.py
# FastAPI webhook Asaas — recebe notificações de pagamento
# Rodar separado: uvicorn src.payments.webhook:app --port 8000
# ============================================================
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from .service import AsaasService
from .plans import PLANOS, calcular_vencimento

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas_webhook")

app = FastAPI(title="Oráculo Analista — Webhook Asaas")
_svc = AsaasService()


# ── schemas ──────────────────────────────────────────
class ClienteIn(BaseModel):
    nome: str
    email: str
    telefone: str


class CobrancaIn(BaseModel):
    cliente_id: str
    plano: str          # mensal | trimestral | anual
    vencimento_dias: int = 3


class VerificacaoIn(BaseModel):
    payment_id: str


# ── rotas ───────────────────────────────────────────
@app.post("/webhook-pagamento")
async def receber_webhook(request: Request):
    """Recebe notificações de pagamento da Asaas."""
    payload = await request.json()
    logger.info(f"Webhook recebido: {payload}")

    payment_id = payload.get("id")
    status     = payload.get("status")
    customer   = payload.get("customer")

    if not all([payment_id, status, customer]):
        raise HTTPException(400, "Campos obrigatórios ausentes")

    if status not in ("RECEIVED", "CONFIRMED"):
        return {"status": "ignorado", "motivo": f"status '{status}' não requer ação"}

    try:
        cliente = _svc.buscar_cliente(customer)
        email   = cliente.get("email")
        if not email:
            raise HTTPException(404, "E-mail do cliente não encontrado no Asaas")

        # Busca o plano solicitado pelo usuário no banco
        from ..models.base import Session
        from .models import UserAnalisePayment
        with Session() as session:
            user = session.query(UserAnalisePayment).filter_by(email=email).first()
            plano = (user.upgrade_solicitado or "mensal") if user else "mensal"

        ok = _svc.ativar_plano(email=email, plano=plano)
        if not ok:
            raise HTTPException(404, "Usuário não encontrado no banco")

        logger.info(f"Plano '{plano}' ativado para {email} via webhook")
        return {"status": "ativado", "email": email, "plano": plano}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(500, f"Erro interno: {e}")


@app.post("/criar-cliente")
def criar_cliente(req: ClienteIn):
    try:
        return _svc.criar_cliente(req.nome, req.email, req.telefone)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/criar-cobranca")
def criar_cobranca(req: CobrancaIn):
    if req.plano not in PLANOS:
        raise HTTPException(400, f"Plano inválido. Opções: {list(PLANOS)}")
    try:
        return _svc.criar_cobranca_pix(req.cliente_id, req.plano, req.vencimento_dias)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/verificar-pagamento")
def verificar_pagamento(req: VerificacaoIn):
    try:
        dados  = _svc.verificar_pagamento(req.payment_id)
        status = dados.get("status", "")
        return {
            **dados,
            "status_pt": AsaasService.status_pt(status),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/listar-pagamentos")
def listar_pagamentos(status: str | None = None):
    try:
        return {"data": _svc.listar_pagamentos(status)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/health")
def health():
    return {"status": "ok", "service": "oraculo-asaas-webhook"}
