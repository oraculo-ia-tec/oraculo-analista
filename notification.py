import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class Notificador:
    def __init__(self, smtp_server, smtp_port, login, senha):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.login = login
        self.senha = senha

    def enviar_email(self, destino, assunto, mensagem):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.login
            msg['To'] = destino
            msg['Subject'] = assunto

            msg.attach(MIMEText(mensagem, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.login, self.senha)
                server.send_message(msg)

            logging.info(f"Email enviado para {destino}")
        except Exception as e:
            logging.error(f"Erro ao enviar email: {e}")

    def enviar_confirmacao_agendamento(self, nome, email, data, hora):
        assunto = "Confirmação de Agendamento - Oráculo Analista"
        mensagem = f"""
        <h3>Olá {nome},</h3>
        <p>Seu agendamento foi confirmado para <strong>{data}</strong> às <strong>{hora}</strong>.</p>
        <p>Nos vemos em breve!</p>
        """
        self.enviar_email(email, assunto, mensagem)

    def enviar_confirmacao_pagamento(self, nome, email, plano):
        assunto = "Pagamento Confirmado - Oráculo Analista"
        mensagem = f"""
        <h3>Olá {nome},</h3>
        <p>Seu pagamento do plano <strong>{plano}</strong> foi confirmado com sucesso.</p>
        <p>Você já pode acessar o Oráculo Analista com todos os recursos liberados.</p>
        """
        self.enviar_email(email, assunto, mensagem)

# Simulação de API de WhatsApp
class WhatsAppSimulado:
    def __init__(self):
        self.envios = []

    def enviar_mensagem(self, numero, mensagem):
        envio = {
            'para': numero,
            'mensagem': mensagem,
            'data': datetime.now().isoformat()
        }
        self.envios.append(envio)
        logging.info(f"Mensagem enviada para {numero}: {mensagem}")

    def confirmar_pagamento_upgrade(self, nome, numero, plano):
        mensagem = f"Olá {nome}, seu pagamento do plano {plano} foi confirmado. Acesso liberado ao Oráculo Analista."
        self.enviar_mensagem(numero, mensagem)

    def confirmar_agendamento(self, nome, numero, data, hora):
        mensagem = f"Olá {nome}, seu agendamento foi confirmado para {data} às {hora}. Estamos esperando você!"
        self.enviar_mensagem(numero, mensagem)
