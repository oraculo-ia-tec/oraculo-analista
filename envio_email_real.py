from notification import Notificador

if __name__ == "__main__":
    notificador = Notificador()
    destino = "williamllider@gmail.com"
    assunto = "Teste real de envio - Oráculo Analista"
    mensagem = """
    <h3>Olá William,</h3>
    <p>Este é um teste real de envio de e-mail usando a integração Gmail API do Oráculo Analista.</p>
    <p>Se você recebeu este e-mail, o envio está funcionando corretamente.</p>
    """
    try:
        resposta = notificador.enviar_email(destino, assunto, mensagem)
        print(f"E-mail enviado com sucesso! ID: {resposta.get('id')}")
    except Exception as e:
        print(f"Falha ao enviar e-mail: {e}")
