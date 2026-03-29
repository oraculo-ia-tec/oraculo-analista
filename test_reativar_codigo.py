import unittest
from unittest.mock import patch, MagicMock
from notification import Notificador

class TestReenviarCodigo(unittest.TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.name = "Usuário Teste"
        self.user.email = "williamllider@gmail.com"
        self.user.verification_code = "123456"

    @patch.object(Notificador, 'enviar_email')
    def test_envio_conteudo_email(self, mock_enviar_email):
        notificador = Notificador()
        assunto = "Código de Verificação - Oráculo Analista"
        mensagem = f"""
        <h3>Olá {self.user.name},</h3>
        <p>Seu novo código de verificação para o Oráculo Analista é:
        <strong>{self.user.verification_code}</strong></p>
        <p>Use este código para ativar sua conta.</p>
        """
        notificador.enviar_email(self.user.email, assunto, mensagem)
        mock_enviar_email.assert_called_once()
        called_email, called_assunto, called_mensagem = mock_enviar_email.call_args[0]
        self.assertEqual(called_email, self.user.email)
        self.assertIn(self.user.verification_code, called_mensagem)
        self.assertIn(self.user.name, called_mensagem)
        self.assertIn("Oráculo Analista", called_assunto)

if __name__ == "__main__":
    unittest.main()
