import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Notificador:
    def __init__(self):
        email_secrets = st.secrets["email"] if "email" in st.secrets else {}

        self.host = email_secrets.get("EMAIL_HOST") or os.getenv("EMAIL_HOST")
        self.port = int(email_secrets.get("EMAIL_PORT") or os.getenv("EMAIL_PORT", "465"))
        self.username = email_secrets.get("EMAIL_USERNAME") or os.getenv("EMAIL_USERNAME")
        self.password = email_secrets.get("EMAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD")
        self.use_tls = str(
            email_secrets.get("EMAIL_USE_TLS") or os.getenv("EMAIL_USE_TLS", "false")
        ).lower() == "true"
        self.use_ssl = str(
            email_secrets.get("EMAIL_USE_SSL") or os.getenv("EMAIL_USE_SSL", "true")
        ).lower() == "true"
        self.remetente = (
            email_secrets.get("EMAIL_REMETENTE")
            or os.getenv("EMAIL_REMETENTE")
            or self.username
        )

    def _validate_settings(self):
        faltantes = [
            nome for nome, valor in {
                "EMAIL_HOST": self.host,
                "EMAIL_USERNAME": self.username,
                "EMAIL_PASSWORD": self.password,
                "EMAIL_REMETENTE": self.remetente,
            }.items()
            if not valor
        ]

        if faltantes:
            raise RuntimeError(
                f"Variáveis SMTP obrigatórias ausentes: {', '.join(faltantes)}"
            )

        if self.use_ssl and self.use_tls:
            raise RuntimeError(
                "EMAIL_USE_SSL e EMAIL_USE_TLS não podem ser true ao mesmo tempo."
            )

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> dict:
        self._validate_settings()

        mail = MIMEMultipart()
        mail["From"] = self.remetente
        mail["To"] = destino
        mail["Subject"] = assunto
        mail.attach(MIMEText(mensagem, "html", "utf-8"))

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=30) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, [destino], mail.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                    server.ehlo()
                    if self.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, [destino], mail.as_string())

            logger.info("E-mail de verificação enviado para %s", destino)
            return {"status": "enviado", "destino": destino}

        except smtplib.SMTPAuthenticationError as exc:
            logger.exception("Falha de autenticação SMTP")
            raise RuntimeError(
                "Falha de autenticação SMTP. Confira usuário e senha da caixa de e-mail."
            ) from exc

        except smtplib.SMTPException as exc:
            logger.exception("Falha SMTP ao enviar e-mail")
            raise RuntimeError(f"Falha SMTP ao enviar e-mail: {exc}") from exc
