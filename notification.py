import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

logging.basicConfig(level=logging.INFO)


class Notificador:
    def __init__(self):
        email_secrets = st.secrets.get("email", {})

        self.host = email_secrets.get("EMAIL_HOST") or os.getenv("EMAIL_HOST", "smtp.hostinger.com")
        self.port = int(email_secrets.get("EMAIL_PORT") or os.getenv("EMAIL_PORT", 465))
        self.username = email_secrets.get("EMAIL_USERNAME") or os.getenv("EMAIL_USERNAME", "")
        self.password = email_secrets.get("EMAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")
        self.use_tls = str(email_secrets.get("EMAIL_USE_TLS") or os.getenv("EMAIL_USE_TLS", "false")).lower() == "true"
        self.use_ssl = str(email_secrets.get("EMAIL_USE_SSL") or os.getenv("EMAIL_USE_SSL", "true")).lower() == "true"
        self.remetente = email_secrets.get("EMAIL_REMETENTE") or os.getenv("EMAIL_REMETENTE", self.username)

    def _validate_settings(self) -> None:
        faltantes = [
            nome for nome, valor in {
                "EMAIL_HOST": self.host,
                "EMAIL_USERNAME": self.username,
                "EMAIL_PASSWORD": self.password,
            }.items() if not valor
        ]
        if faltantes:
            raise RuntimeError(
                f"Variáveis obrigatórias ausentes para envio de e-mail: {', '.join(faltantes)}"
            )

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> bool:
        """Envia e-mail via SMTP Hostinger (SSL ou TLS)."""
        self._validate_settings()

        mime = MIMEMultipart("alternative")
        mime["To"] = destino
        mime["From"] = self.remetente
        mime["Subject"] = assunto
        mime.attach(MIMEText(mensagem, "html", "utf-8"))

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, destino, mime.as_string())
            else:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.ehlo()
                    if self.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, destino, mime.as_string())

            logging.info(f"E-mail enviado com sucesso para {destino}.")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logging.exception(f"Erro de autenticação SMTP: {e}")
            raise RuntimeError("Falha na autenticação SMTP. Verifique EMAIL_USERNAME e EMAIL_PASSWORD.") from e

        except smtplib.SMTPException as e:
            logging.exception(f"Erro SMTP ao enviar para {destino}: {e}")
            raise RuntimeError(f"Erro SMTP: {e}") from e

        except Exception as e:
            logging.exception(f"Erro inesperado ao enviar e-mail para {destino}: {e}")
            raise RuntimeError(f"Falha no envio de e-mail: {e}") from e

    # ------------------------------------------------------------------
    # Métodos de notificação específicos
    # ------------------------------------------------------------------

    def enviar_recuperacao_senha(self, nome: str, email: str, link: str) -> bool:
        """Envia link seguro para redefinição de senha (expira em 60 min)."""
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
              Se você não solicitou a redefinição, ignore este e-mail.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_senha_alterada(self, nome: str, email: str) -> bool:
        """Notifica que a senha foi alterada com sucesso."""
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
              Em seguida, você receberá um código de verificação para confirmar o acesso.
            </p>
            <p style="color:#6b7280;font-size:13px;">
              Se você não realizou esta alteração, entre em contato com nosso suporte imediatamente.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_verificacao(self, nome: str, email: str, codigo: str) -> bool:
        """Envia código de verificação de 6 dígitos."""
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
              ⚠️ Nunca compartilhe este código com ninguém.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">
              Oráculo Analista · Oráculos AI
            </p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_boas_vindas(self, nome: str, email: str, whatsapp: str) -> bool:
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
              📱 WhatsApp: <strong>{whatsapp}</strong><br>
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
