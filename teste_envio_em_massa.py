from notification import Notificador

USUARIOS = [
    (1, 'William Eustáquio', 'programador.descpro@gmail.com'),
    (3, "T'Challa (Pantera Negra)", 'rededescpro@gmail.com'),
    (4, 'Cliente', 'ferragensefraim@gmail.com'),
]

if __name__ == "__main__":
    notificador = Notificador()
    assunto = "Teste em massa - Oráculo Analista"
    for id_, nome, email in USUARIOS:
        mensagem = f"""
        <h3>Olá {nome},</h3>
        <p>Este é um teste de envio em massa do Oráculo Analista.</p>
        <p>Se você recebeu este e-mail, o envio está funcionando corretamente.</p>
        """
        try:
            resposta = notificador.enviar_email(email, assunto, mensagem)
            print(f"E-mail enviado para {email}! ID: {resposta.get('id')}")
        except Exception as e:
            print(f"Falha ao enviar para {email}: {e}")
