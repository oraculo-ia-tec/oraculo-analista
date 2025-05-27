from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decouple import config
from datetime import datetime, timedelta, date
from pagamentos import Base, UserAnalise
from pydantic import BaseModel
import requests
import logging

app = FastAPI()

# Configuração do banco de dados
DATABASE_URL = config("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Configuração da API ASAAS
ASAAS_API_KEY = config("ASAAS_API_KEY")
BASE_URL_ASAAS = config("BASE_URL_ASAAS")
HEADERS = {
    "Content-Type": "application/json",
    "access_token": ASAAS_API_KEY
}

# Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas_api")

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

# Webhook de notificação automática de pagamento
@app.post("/webhook-pagamento")
async def receber_webhook_pagamento(request: Request):
    payload = await request.json()

    payment_id = payload.get("id")
    status = payload.get("status")
    customer = payload.get("customer")

    if not all([payment_id, status, customer]):
        raise HTTPException(status_code=400, detail="Campos obrigatórios ausentes no payload")

    try:
        cliente_resp = requests.get(f"{BASE_URL_ASAAS}/customers/{customer}", headers=HEADERS)
        if cliente_resp.status_code != 200:
            raise HTTPException(status_code=cliente_resp.status_code, detail="Erro ao buscar cliente no Asaas")

        email_cliente = cliente_resp.json().get("email")
        if not email_cliente:
            raise HTTPException(status_code=404, detail="E-mail do cliente não localizado no Asaas")

        if status == "RECEIVED":
            session = Session()
            usuario = session.query(UserAnalise).filter_by(email=email_cliente).first()

            if usuario:
                usuario.pagamento_confirmado = True
                usuario.acesso_autorizado = True
                usuario.plano = usuario.upgrade_solicitado

                dias = 30 if usuario.plano == "mensal" else 90 if usuario.plano == "trimestral" else 365
                usuario.data_vencimento = datetime.now().date() + timedelta(days=dias)
                usuario.upgrade_solicitado = None

                session.commit()
                session.close()
                return {"status": "atualizado", "cliente": usuario.email, "pagamento": "confirmado"}
            else:
                session.close()
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return {"status": "ignorado", "motivo": f"Status '{status}' não requer atualização"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no webhook: {str(e)}")

# Rotas auxiliares
@app.post("/criar-cliente")
def criar_cliente_api(req: ClienteRequest):
    payload = {
        "name": req.nome,
        "email": req.email,
        "mobilePhone": req.telefone
    }
    logger.info(f"Criando cliente: {payload}")
    response = requests.post(f"{BASE_URL_ASAAS}/customers", json=payload, headers=HEADERS)
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
    response = requests.post(f"{BASE_URL_ASAAS}/payments", json=payload, headers=HEADERS)
    logger.info(f"Resposta ASAAS - criar_cobranca: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.post("/verificar-pagamento")
def verificar_pagamento_api(req: VerificacaoRequest):
    logger.info(f"Verificando pagamento ID: {req.payment_id}")
    response = requests.get(f"{BASE_URL_ASAAS}/payments/{req.payment_id}", headers=HEADERS)
    logger.info(f"Resposta ASAAS - verificar_pagamento: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/listar-pagamentos")
def listar_pagamentos(status: str = None):
    logger.info(f"Listando pagamentos com status: {status}")
    params = {"status": status} if status else {}
    response = requests.get(f"{BASE_URL_ASAAS}/payments", headers=HEADERS, params=params)
    logger.info(f"Resposta ASAAS - listar_pagamentos: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/vencimento/{dias}")
def gerar_vencimento(dias: int = 3):
    data_venc = (date.today() + timedelta(days=dias)).isoformat()
    logger.info(f"Gerando data de vencimento para {dias} dias: {data_venc}")
    return {"vencimento": data_venc}
