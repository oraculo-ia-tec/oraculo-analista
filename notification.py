import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

logging.basicConfig(level=logging.INFO)

SMTP_TIMEOUT = 10  # segundos — evita travar indefinidamente


class Notificador:
    """
    Envia e-mails via SMTP.
    Credenciais lidas via st.secrets["email"].
    """

    def __init__(self):
        email_cfg = st.secrets.get("email", {})
        self.host      = email_cfg.get("EMAIL_HOST", "")
        self.port      = int(email_cfg.get("EMAIL_PORT", 587))
        self.username  = email_cfg.get("EMAIL_USERNAME", "")
        self.password  = email_cfg.get("EMAIL_PASSWORD", "")
        self.use_tls   = bool(email_cfg.get("EMAIL_USE_TLS", True))
        self.use_ssl   = bool(email_cfg.get("EMAIL_USE_SSL", False))
        self.remetente = email_cfg.get("EMAIL_REMETENTE", self.username)

    def _configurado(self) -> bool:
        return bool(self.host and self.username and self.password)

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> dict:
        if not self._configurado():
            logging.warning("SMTP não configurado — e-mail ignorado.")
            return {"status": "skip", "destino": destino}

        mime = MIMEMultipart("alternative")
        mime["From"]    = self.remetente
        mime["To"]      = destino
        mime["Subject"] = assunto
        mime.attach(MIMEText(mensagem, "html", "utf-8"))

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=SMTP_TIMEOUT) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.sendmail(self.remetente, destino, mime.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=SMTP_TIMEOUT) as smtp:
                    if self.use_tls:
                        smtp.starttls()
                    smtp.login(self.username, self.password)
                    smtp.sendmail(self.remetente, destino, mime.as_string())

            logging.info(f"E-mail enviado para {destino}.")
            return {"status": "ok", "destino": destino}

        except smtplib.SMTPAuthenticationError as e:
            logging.error("Falha de autenticação SMTP.")
            raise RuntimeError("Usuário ou senha SMTP inválidos.") from e

        except Exception as e:
            logging.error(f"Erro SMTP para {destino}: {e}")
            raise RuntimeError(f"Falha no envio de e-mail: {e}") from e
