# api_asaas.py - FastAPI API

import requests
from decouple import config
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta

app = FastAPI()

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas_api")

# Chave da API do ASAAS
ASAAS_API_KEY = config("ASAAS_API_KEY")
if not ASAAS_API_KEY:
    raise ValueError("A variável de ambiente ASAAS_API_KEY não está definida. Verifique o arquivo .env.")

logger.info("Chave da API ASAAS carregada com sucesso.")

ASAAS_API_URL = "https://www.asaas.com/api/v3"
HEADERS = {
    "Content-Type": "application/json",
    "access_token": ASAAS_API_KEY
}

# Pydantic Schemas
class ClienteRequest(BaseModel):
    nome: str
    email: str
    telefone: str

class CobrancaRequest(BaseModel):
    cliente_id: str
    valor: float
    vencimento: str  # formato YYYY-MM-DD
    descricao: str = "Plano Oráculo Analista"

class VerificacaoRequest(BaseModel):
    payment_id: str

# Rotas FastAPI
@app.post("/criar-cliente")
def criar_cliente_api(req: ClienteRequest):
    payload = {
        "name": req.nome,
        "email": req.email,
        "mobilePhone": req.telefone
    }
    logger.info(f"Criando cliente: {payload}")
    response = requests.post(f"{ASAAS_API_URL}/customers", json=payload, headers=HEADERS)
    logger.info(f"Resposta ASAAS - criar_cliente: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.post("/criar-cobranca")
def criar_cobranca_api(req: CobrancaRequest):
    payload = {
        "customer": req.cliente_id,
        "billingType": "PIX",
        "value": req.valor,
        "dueDate": req.vencimento,
        "description": req.descricao
    }
    logger.info(f"Criando cobrança: {payload}")
    response = requests.post(f"{ASAAS_API_URL}/payments", json=payload, headers=HEADERS)
    logger.info(f"Resposta ASAAS - criar_cobranca: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.post("/verificar-pagamento")
def verificar_pagamento_api(req: VerificacaoRequest):
    logger.info(f"Verificando pagamento ID: {req.payment_id}")
    response = requests.get(f"{ASAAS_API_URL}/payments/{req.payment_id}", headers=HEADERS)
    logger.info(f"Resposta ASAAS - verificar_pagamento: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/listar-pagamentos")
def listar_pagamentos(status: str = None):
    logger.info(f"Listando pagamentos com status: {status}")
    params = {"status": status} if status else {}
    response = requests.get(f"{ASAAS_API_URL}/payments", headers=HEADERS, params=params)
    logger.info(f"Resposta ASAAS - listar_pagamentos: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

# Utilitário: gerar data de vencimento futura
@app.get("/vencimento/{dias}")
def gerar_vencimento(dias: int = 3):
    data_venc = (date.today() + timedelta(days=dias)).isoformat()
    logger.info(f"Gerando data de vencimento para {dias} dias: {data_venc}")
    return {"vencimento": data_venc}
