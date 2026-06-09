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

        self.host = str(email_secrets.get("EMAIL_HOST") or os.getenv("EMAIL_HOST", "smtp.hostinger.com"))
        self.port = int(email_secrets.get("EMAIL_PORT") or os.getenv("EMAIL_PORT", 465))
        self.username = str(email_secrets.get("EMAIL_USERNAME") or os.getenv("EMAIL_USERNAME", ""))
        self.password = str(email_secrets.get("EMAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD", ""))
        self.remetente = str(email_secrets.get("EMAIL_REMETENTE") or os.getenv("EMAIL_REMETENTE", self.username))

        # Detecta modo pela porta - ignora EMAIL_USE_SSL/TLS para evitar conflito
        # Porta 465 = SSL direto | Porta 587 ou 25 = STARTTLS
        self.use_ssl = self.port == 465

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
                f"Variaveis obrigatorias ausentes para envio de e-mail: {', '.join(faltantes)}"
            )

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> bool:
        """Envia e-mail via SMTP Hostinger com deteccao automatica SSL/TLS."""
        self._validate_settings()

        mime = MIMEMultipart("alternative")
        mime["To"] = destino
        mime["From"] = self.remetente
        mime["Subject"] = assunto
        mime.attach(MIMEText(mensagem, "html", "utf-8"))

        try:
            if self.use_ssl:
                # Porta 465: SSL desde o inicio da conexao
                with smtplib.SMTP_SSL(self.host, self.port) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, destino, mime.as_string())
            else:
                # Porta 587: conexao plaintext + upgrade TLS via STARTTLS
                with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.username, self.password)
                    server.sendmail(self.remetente, destino, mime.as_string())

            logging.info(f"E-mail enviado com sucesso para {destino} via porta {self.port}.")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logging.exception(f"Erro de autenticacao SMTP: {e}")
            raise RuntimeError(
                "Falha na autenticacao SMTP. Verifique EMAIL_USERNAME e EMAIL_PASSWORD nos Secrets."
            ) from e

        except smtplib.SMTPException as e:
            logging.exception(f"Erro SMTP ao enviar para {destino}: {e}")
            raise RuntimeError(f"Erro SMTP: {e}") from e

        except Exception as e:
            logging.exception(f"Erro inesperado ao enviar e-mail para {destino}: {e}")
            raise RuntimeError(f"Falha no envio de e-mail: {e}") from e

    # ------------------------------------------------------------------
    # Metodos de notificacao especificos
    # ------------------------------------------------------------------

    def enviar_recuperacao_senha(self, nome: str, email: str, link: str) -> bool:
        assunto = "Redefinicao de senha - Oraculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;">Redefinicao de Senha</h2>
            <p style="color:#374151;">Ola, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Clique no botao abaixo para criar uma nova senha no Oraculo Analista:
            </p>
            <div style="text-align:center;margin:32px 0;">
              <a href="{link}" style="background:#7c3aed;color:#fff;text-decoration:none;
                        padding:14px 32px;border-radius:8px;font-size:16px;
                        font-weight:600;display:inline-block;">Criar Nova Senha</a>
            </div>
            <p style="color:#6b7280;font-size:13px;">
              Ou copie este link no navegador:<br>
              <a href="{link}" style="color:#7c3aed;word-break:break-all;">{link}</a>
            </p>
            <p style="color:#6b7280;font-size:13px;margin-top:16px;">
              Este link expira em <strong>60 minutos</strong>.
              Se voce nao solicitou, ignore este e-mail.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">Oraculo Analista - Oraculos AI</p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_senha_alterada(self, nome: str, email: str) -> bool:
        assunto = "Senha alterada com sucesso - Oraculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#059669;">Senha Alterada com Sucesso</h2>
            <p style="color:#374151;">Ola, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Sua senha no Oraculo Analista foi redefinida com sucesso.
              Voce recebera em seguida um codigo de verificacao para acessar o sistema.
            </p>
            <p style="color:#6b7280;font-size:13px;">
              Se voce nao realizou esta alteracao, entre em contato com o suporte imediatamente.
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">Oraculo Analista - Oraculos AI</p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_verificacao(self, nome: str, email: str, codigo: str) -> bool:
        assunto = "Codigo de verificacao - Oraculo Analista"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;">Codigo de Verificacao</h2>
            <p style="color:#374151;">Ola, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">Use o codigo abaixo para confirmar seu acesso ao Oraculo Analista:</p>
            <div style="text-align:center;margin:32px 0;">
              <span style="font-size:40px;font-weight:800;letter-spacing:12px;
                           color:#7c3aed;background:#f3f0ff;padding:16px 32px;
                           border-radius:12px;display:inline-block;">{codigo}</span>
            </div>
            <p style="color:#6b7280;font-size:13px;">Nunca compartilhe este codigo com ninguem.</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">Oraculo Analista - Oraculos AI</p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)

    def enviar_boas_vindas(self, nome: str, email: str, whatsapp: str) -> bool:
        assunto = "Bem-vindo ao Oraculo Analista!"
        mensagem = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
                      padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            <h2 style="color:#7c3aed;">Bem-vindo(a)!</h2>
            <p style="color:#374151;">Ola, <strong>{nome}</strong>!</p>
            <p style="color:#374151;">
              Sua conta no Oraculo Analista foi criada com sucesso.
              Voce recebera em instantes um codigo de verificacao para ativar seu acesso.
            </p>
            <p style="color:#374151;">
              WhatsApp: <strong>{whatsapp}</strong><br>
              E-mail: <strong>{email}</strong>
            </p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;text-align:center;">Oraculo Analista - Oraculos AI</p>
          </div>
        </body></html>
        """
        return self.enviar_email(destino=email, assunto=assunto, mensagem=mensagem)
