"""
Gera o GMAIL_REFRESH_TOKEN usando as credenciais do .streamlit/secrets.toml
e atualiza automaticamente:
  - .streamlit/secrets.toml
  - .env
  - tokens.json

Uso:
    python gerar_refresh_token_gmail.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import toml
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).parent
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"
ENV_PATH = ROOT / ".env"
TOKENS_PATH = ROOT / "tokens.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.insert",
]


def carregar_credenciais() -> tuple[str, str, int, str]:
    if not SECRETS_PATH.exists():
        sys.exit(f"❌ Arquivo não encontrado: {SECRETS_PATH}")

    data = toml.load(SECRETS_PATH)
    email_cfg = data.get("email", {})
    client_id = email_cfg.get("GOOGLE_CLIENT_ID")
    client_secret = email_cfg.get("GOOGLE_CLIENT_SECRET")
    port = int(email_cfg.get("GOOGLE_AUTH_PORT", 8765))
    redirect_uri = email_cfg.get(
        "GOOGLE_REDIRECT_URI", f"http://127.0.0.1:{port}/")

    if not client_id or not client_secret:
        sys.exit(
            "❌ GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET ausentes na seção [email] do secrets.toml")

    return client_id, client_secret, port, redirect_uri


def atualizar_secrets_toml(refresh_token: str) -> None:
    text = SECRETS_PATH.read_text(encoding="utf-8")
    novo, n = re.subn(
        r'^GMAIL_REFRESH_TOKEN\s*=\s*".*"',
        f'GMAIL_REFRESH_TOKEN = "{refresh_token}"',
        text,
        flags=re.MULTILINE,
    )
    if n == 0:
        novo = text.rstrip() + \
            f'\nGMAIL_REFRESH_TOKEN = "{refresh_token}"\n'
    SECRETS_PATH.write_text(novo, encoding="utf-8")
    print("✅ secrets.toml atualizado")


def atualizar_env(refresh_token: str) -> None:
    if not ENV_PATH.exists():
        return
    text = ENV_PATH.read_text(encoding="utf-8")
    novo, n = re.subn(
        r'^GMAIL_REFRESH_TOKEN\s*=.*$',
        f'GMAIL_REFRESH_TOKEN={refresh_token}',
        text,
        flags=re.MULTILINE,
    )
    if n == 0:
        novo = text.rstrip() + f'\nGMAIL_REFRESH_TOKEN={refresh_token}\n'
    ENV_PATH.write_text(novo, encoding="utf-8")
    print("✅ .env atualizado")


def atualizar_tokens_json(creds) -> None:
    payload = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_type": "Bearer",
        "expires_in": 3599,
        "scope": " ".join(creds.scopes or SCOPES),
    }
    TOKENS_PATH.write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    print("✅ tokens.json atualizado")


def main() -> None:
    client_id, client_secret, port, redirect_uri = carregar_credenciais()

    print(f"🔐 Client ID: {client_id[:30]}...")
    print(f"🔐 Porta: {port}")
    print(f"🔐 Redirect URI: {redirect_uri}")
    print()
    print("👉 Abrindo navegador para autorização.")
    print("   Faça login com a conta CORRETA (oraculoiatec@gmail.com).")
    print()

    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    creds = flow.run_local_server(
        port=port,
        access_type="offline",
        prompt="consent",
    )

    if not creds.refresh_token:
        sys.exit(
            "❌ Refresh token não retornado. Acesse "
            "https://myaccount.google.com/permissions, remova o app "
            "e rode novamente.")

    print()
    print(f"🎉 Refresh token gerado: {creds.refresh_token[:40]}...")
    print()
    atualizar_secrets_toml(creds.refresh_token)
    atualizar_env(creds.refresh_token)
    atualizar_tokens_json(creds)
    print()
    print("✅ Pronto! Reinicie o Streamlit para aplicar as novas credenciais.")


if __name__ == "__main__":
    main()
