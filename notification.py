import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

logging.basicConfig(level=logging.INFO)


class Notificador:
    """
    Envia e-mails via SMTP (Hostinger ou qualquer servidor SMTP).
    Credenciais lidas exclusivamente via st.secrets["email"].
    """

    def __init__(self):
        email_cfg = st.secrets.get("email", {})

        self.host       = email_cfg.get("EMAIL_HOST", "")
        self.port       = int(email_cfg.get("EMAIL_PORT", 587))
        self.username   = email_cfg.get("EMAIL_USERNAME", "")
        self.password   = email_cfg.get("EMAIL_PASSWORD", "")
        self.use_tls    = bool(email_cfg.get("EMAIL_USE_TLS", True))
        self.use_ssl    = bool(email_cfg.get("EMAIL_USE_SSL", False))
        self.remetente  = email_cfg.get("EMAIL_REMETENTE", self.username)

    def _validate_settings(self) -> None:
        faltantes = [
            nome for nome, valor in {
                "EMAIL_HOST":     self.host,
                "EMAIL_USERNAME": self.username,
                "EMAIL_PASSWORD": self.password,
            }.items() if not valor
        ]
        if faltantes:
            raise RuntimeError(
                f"Variáveis obrigatórias ausentes para SMTP: {', '.join(faltantes)}"
            )

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> dict:
        """
        Envia um e-mail HTML via SMTP.

        Args:
            destino:  Endereço de destino.
            assunto:  Assunto do e-mail.
            mensagem: Corpo em HTML.

        Returns:
            dict com 'status' e 'destino'.
        """
        self._validate_settings()

        mime = MIMEMultipart("alternative")
        mime["From"]    = self.remetente
        mime["To"]      = destino
        mime["Subject"] = assunto
        mime.attach(MIMEText(mensagem, "html", "utf-8"))

        try:
            if self.use_ssl:
                # Porta 465 — SSL direto
                with smtplib.SMTP_SSL(self.host, self.port) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.sendmail(self.remetente, destino, mime.as_string())
            else:
                # Porta 587 — STARTTLS (padrão Hostinger)
                with smtplib.SMTP(self.host, self.port) as smtp:
                    if self.use_tls:
                        smtp.starttls()
                    smtp.login(self.username, self.password)
                    smtp.sendmail(self.remetente, destino, mime.as_string())

            logging.info(f"E-mail enviado com sucesso para {destino}.")
            return {"status": "ok", "destino": destino}

        except smtplib.SMTPAuthenticationError as e:
            logging.exception("Falha de autenticação SMTP.")
            raise RuntimeError("Usuário ou senha SMTP inválidos.") from e

        except smtplib.SMTPException as e:
            logging.exception(f"Erro SMTP ao enviar para {destino}.")
            raise RuntimeError(f"Falha no envio via SMTP: {e}") from e

        except Exception as e:
            logging.exception(f"Erro inesperado ao enviar e-mail para {destino}.")
            raise RuntimeError(f"Erro desconhecido no envio de e-mail: {e}") from e
