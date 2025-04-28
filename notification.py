import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string


# Configurações de e-mail (substitua pelos seus dados)
SMTP_SERVER = "smtp.seu_servidor.com"  # Exemplo: smtp.gmail.com
SMTP_PORT = 587
EMAIL_SENDER = "seu_email@gmail.com"  # E-mail do remetente
EMAIL_PASSWORD = "sua_senha"          # Senha do e-mail
ADMIN_EMAIL = "admin@seusistema.com"  # E-mail do administrador


# Função para enviar e-mail de verificação ao usuário
def enviar_email_verificacao(destinatario, codigo):
    try:
        # Criar mensagem
        assunto = "Confirmação de Cadastro - Oráculo Analista"
        corpo = f"""
        Olá!

        Obrigado por se cadastrar no Oráculo Analista. Para confirmar seu cadastro, use o código abaixo:

        Código de Verificação: {codigo}

        Insira este código no sistema para ativar sua conta.

        Atenciosamente,
        Equipe Oráculo Analista
        """

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        # Enviar e-mail
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, destinatario, msg.as_string())

        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de verificação: {str(e)}")
        return False


# Função para enviar notificação ao administrador
def notificar_admin(nome_usuario, email_usuario):
    try:
        # Criar mensagem
        assunto = "Novo Usuário Cadastrado - Oráculo Analista"
        corpo = f"""
        Olá Administrador,

        Um novo usuário foi cadastrado no sistema Oráculo Analista:

        Nome: {nome_usuario}
        E-mail: {email_usuario}

        Por favor, revise o cadastro e tome as providências necessárias.

        Atenciosamente,
        Sistema Oráculo Analista
        """

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        # Enviar e-mail
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, msg.as_string())

        return True
    except Exception as e:
        print(f"Erro ao notificar administrador: {str(e)}")
        return False