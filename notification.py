import os
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import streamlit as st

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Dependências da Gmail API não instaladas. "
        "Adicione ao requirements.txt: "
        "google-api-python-client, google-auth, "
        "google-auth-oauthlib, google-auth-httplib2"
    ) from e

logging.basicConfig(level=logging.INFO)


class Notificador:
    def __init__(self):
        email_secrets = st.secrets["email"] if "email" in st.secrets else {}

        self.google_client_id = email_secrets.get(
            "GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = email_secrets.get(
            "GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_refresh_token = email_secrets.get(
            "GMAIL_REFRESH_TOKEN") or os.getenv("GMAIL_REFRESH_TOKEN")
        self.google_oauth_scopes_raw = email_secrets.get(
            "GOOGLE_OAUTH_SCOPES") or os.getenv("GOOGLE_OAUTH_SCOPES", "")
        self.login = email_secrets.get(
            "EMAIL_REMETENTE") or os.getenv("EMAIL_REMETENTE")

        self.google_scopes = self._load_scopes()

    def _load_scopes(self) -> List[str]:
        if self.google_oauth_scopes_raw.strip():
            scopes = [
                scope.strip()
                for scope in self.google_oauth_scopes_raw.split()
                if scope.strip()
            ]
            return scopes

        return ["https://www.googleapis.com/auth/gmail.send"]

    def _validate_settings(self) -> None:
        faltantes = [
            nome for nome, valor in {
                "GOOGLE_CLIENT_ID": self.google_client_id,
                "GOOGLE_CLIENT_SECRET": self.google_client_secret,
                "GMAIL_REFRESH_TOKEN": self.google_refresh_token,
            }.items() if not valor
        ]

        if faltantes:
            raise RuntimeError(
                f"Variáveis obrigatórias ausentes para Gmail API: {', '.join(faltantes)}"
            )

    def _build_credentials(self) -> Credentials:
        self._validate_settings()

        return Credentials(
            token=None,
            refresh_token=self.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.google_client_id,
            client_secret=self.google_client_secret,
            scopes=self.google_scopes,
        )

    def _build_service(self):
        creds = self._build_credentials()
        return build("gmail", "v1", credentials=creds)

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> dict:
        try:
            service = self._build_service()

            mime_message = MIMEMultipart()
            mime_message["To"] = destino
            mime_message["From"] = self.login or "me"
            mime_message["Subject"] = assunto
            mime_message.attach(MIMEText(mensagem, "html", "utf-8"))

            raw_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()
            ).decode("utf-8")

            body = {"raw": raw_message}

            response = (
                service.users()
                .messages()
                .send(userId="me", body=body)
                .execute()
            )

            logging.info(
                f"E-mail enviado com sucesso para {destino}. ID: {response.get('id')}")
            return response

        except HttpError as e:
            logging.exception(
                f"Erro HTTP da Gmail API ao enviar para {destino}: {e}")
            raise RuntimeError(
                f"Erro da Gmail API ao enviar e-mail: {e}") from e

        except Exception as e:
            logging.exception(
                f"Erro inesperado ao enviar e-mail para {destino}: {e}")
            raise RuntimeError(f"Falha no envio de e-mail: {e}") from e
