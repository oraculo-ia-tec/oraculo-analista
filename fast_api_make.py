from fastapi import FastAPI, HTTPException
import requests
from decouple import config

# Configurações do Webhook do Make
MAKE_WEBHOOK_URL = config("MAKE_WEBHOOK_URL")  # URL do webhook do Make

app = FastAPI()

@app.post("/register/")
async def register_user(data: dict):
    """
    Endpoint para receber dados de cadastro e enviar ao webhook do Make.
    """
    try:
        # Extrair dados do payload
        name = data.get("name")
        email = data.get("email")
        whatsapp = data.get("whatsapp")

        if not all([name, email, whatsapp]):
            raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios.")

        # Enviar dados ao webhook do Make
        response = requests.post(MAKE_WEBHOOK_URL, json=data)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro ao enviar dados ao Make.")

        return {"message": "Dados enviados ao Make com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))