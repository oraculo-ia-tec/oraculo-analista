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
        """Método base para envio via Gmail API."""
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

    # ------------------------------------------------------------------
    # Métodos de notificação específicos
    # ------------------------------------------------------------------

    def enviar_recuperacao_senha(self, nome: str, email: str, link: str) -> dict:
        """Envia e-mail com link seguro para redefinição de senha (expira em 60 min)."""
        assunto = "🔑 Redefinição de senha — Oráculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;margin-bottom:8px;">🔑 Redefinição de Senha</h2>
            <p style="color:#374151;">Olá, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Recebemos uma solicitação para redefinir a senha da sua conta no
              <strong>Oráculo Analista</strong>.
              Clique no botão abaixo para criar uma nova senha:
            </p>
            <div style="text-align:center;margin:32px 0;">
              <a href="{link}"
                 style="background:#7c3aed;color:#fff;text-decoration:none;
                        padding:14px 32px;border-radius:8px;font-size:16px;
                        font-weight:600;display:inline-block;">
                Criar Nova Senha
              </a>
            </div>
            <p style="color:#6b7280;font-size:13px;">
              Caso o botão não funcione, copie e cole o link abaixo no navegador:<br>
              <a href="{link}" style="color:#7c3aed;word-break:break-all;">{link}</a>
            </p>
            <p style="color:#6b7280;font-size:13px;margin-top:16px;">
              ⚠️ Este link expira em <strong>60 minutos</strong>.
              Se você não solicitou a redefinição, ignore este e-mail — sua senha não será alterada.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_senha_alterada(self, nome: str, email: str) -> dict:
        """Notifica o usuário que sua senha foi alterada com sucesso."""
        assunto = "✅ Senha alterada com sucesso — Oráculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#059669;margin-bottom:8px;">✅ Senha Alterada</h2>
            <p style="color:#374151;">Olá, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Sua senha no <strong>Oráculo Analista</strong> foi redefinida com sucesso.
            </p>
            <p style="color:#374151;">
              Em seguida, você receberá um código de verificação para confirmar o acesso ao sistema.
            </p>
            <p style="color:#6b7280;font-size:13px;">
              Se você não realizou esta alteração, entre em contato imediatamente com nosso suporte.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_verificacao(self, nome: str, email: str, codigo: str) -> dict:
        """Envia código de verificação 6 dígitos para confirmar acesso."""
        assunto = "🔐 Código de verificação — Oráculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;margin-bottom:8px;">🔐 Código de Verificação</h2>
            <p style="color:#374151;">Olá, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Use o código abaixo para confirmar seu acesso ao
              <strong>Oráculo Analista</strong>:
            </p>
            <div style="text-align:center;margin:32px 0;">
              <span style="font-size:40px;font-weight:800;letter-spacing:12px;
                           color:#7c3aed;background:#f3f0ff;padding:16px 32px;
                           border-radius:12px;display:inline-block;">
                {codigo}
              </span>
            </div>
            <p style="color:#6b7280;font-size:13px;">
              ⚠️ Nunca compartilhe este código. Se você não solicitou este acesso,
              ignore este e-mail.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_boas_vindas(self, nome: str, email: str, whatsapp: str) -> dict:
        """Envia e-mail de boas-vindas após o cadastro."""
        assunto = "🎉 Bem-vindo ao Oráculo Analista!"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;margin-bottom:8px;">🎉 Bem-vindo(a)!</h2>
            <p style="color:#374151;">Olá, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Sua conta no <strong>Oráculo Analista</strong> foi criada com sucesso.
              Você receberá em instantes um código de verificação para ativar seu acesso.
            </p>
            <p style="color:#374151;">
              📱 WhatsApp cadastrado: <strong>{whatsapp}</strong><br>
              📧 E-mail: <strong>{email}</strong>
            </p>
            <p style="color:#6b7280;font-size:13px;">
              Qualquer dúvida, entre em contato com nosso suporte.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)
