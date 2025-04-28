import os
import replicate
from decouple import config

# Verificar se o token está configurado
REPLICATE_API_TOKEN = "r8_9qyeytR9OiIobAQ1f0TzU3TGKJBLSzI0ti8Jp"
if not REPLICATE_API_TOKEN:
    raise ValueError("Token da API do Replicate não configurado. Verifique o arquivo .env.")


# Testar a conexão com o Replicate
try:
    output = replicate.run(
        "deepseek-ai/deepseek-r1",
        input={
            "top_p": 1,
            "prompt": "Teste de conexão",
            "max_tokens": 50,
            "temperature": 0.1,
        },
    )
    print("Resposta do Replicate:", output)
except Exception as e:
    print(f"Erro ao conectar ao Replicate: {str(e)}")