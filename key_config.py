from decouple import config

# URL base da API do Stripe
URL_BASE = "https://api.stripe.com/v1"
BASE_URL_ASAAS = "https://api-sandbox.asaas.com/v3"

# Chave da API do Banco de Dados
DATABASE_URL = config("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não está definida. Verifique o arquivo .env.")

# Chave da API do Stripe
API_KEY_STRIPE = config("API_KEY_STRIPE")
if not API_KEY_STRIPE:
    raise ValueError("A variável de ambiente API_KEY_STRIPE não está definida. Verifique o arquivo .env.")

# Chave da API do REPLICATE
REPLICATE_API_TOKEN = config("REPLICATE_API_TOKEN")  # Altere aqui para usar o nome correto
if not REPLICATE_API_TOKEN:
    raise ValueError("A variável de ambiente REPLICATE_API_TOKEN não está definida. Verifique o arquivo .env.")

# Chave da API do ASAAS
ASAAS_API_KEY = config("ASAAS_API_KEY")
if not ASAAS_API_KEY:
    raise ValueError("A variável de ambiente ASAAS_API_KEY não está definida. Verifique o arquivo .env.")

# Chave do Webhook do Stripe
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET")
if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("A variável de ambiente STRIPE_WEBHOOK_SECRET não está definida. Verifique o arquivo .env.")

# Chave do Webhook do MAKE TESTE
WEBHOOK_TESTE = config("WEBHOOK_TESTE")
if not WEBHOOK_TESTE:
    raise ValueError("A variável de ambiente WEBHOOK_TESTE não está definida. Verifique o arquivo .env.")

# Chave do Webhook do MAKE CADASTRO
WEBHOOK_CADASTRO_ANALISTA = config("WEBHOOK_CADASTRO_ANALISTA")
if not WEBHOOK_CADASTRO_ANALISTA:
    raise ValueError("A variável de ambiente WEBHOOK_CADASTRO_ANALISTA não está definida. Verifique o arquivo .env.")

# URL da API FastAPI
FASTAPI_URL = config("FASTAPI_URL")
if not FASTAPI_URL:
    raise ValueError("A variável de ambiente FASTAPI_URL não está definida. Verifique o arquivo .env.")