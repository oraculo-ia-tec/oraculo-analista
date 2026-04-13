import base64
import json
import logging
import os
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import AutoConfig
from google.auth.exceptions import RefreshError

try:
    import streamlit as st
except Exception:
    st = None

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except Exception:
    Credentials = None
    build = None


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
config = AutoConfig(search_path='.')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'src', 'img', 'perfil-analista.png')


def get_setting(key: str, default=None):
    if st is not None:
        try:
            if key in st.secrets:
                value = st.secrets[key]
                if hasattr(value, 'to_dict'):
                    return value.to_dict()
                return value
        except Exception:
            pass

    try:
        value = config(key, default=None)
        if value is not None:
            return value
    except Exception:
        pass

    return os.getenv(key, default)


class Notificador:
    """
    Envia e-mails pela Gmail API usando service account com delegação.

    Configuração esperada em st.secrets ou .env:
    - GMAIL_DELEGATED_USER: e-mail do usuário Workspace a ser impersonado
    - GMAIL_SENDER_EMAIL: opcional, remetente exibido no cabeçalho From
    - GMAIL_SERVICE_ACCOUNT_INFO: JSON completo como string
      ou tabela/dict em secrets.toml
    - GMAIL_SERVICE_ACCOUNT_FILE: caminho do arquivo JSON (fallback)

    Observação importante:
    Service account com Gmail API exige Google Workspace + Domain-Wide Delegation.
    Contas Gmail pessoais normalmente não funcionam com esse fluxo.
    """

    def __init__(self):
        self.delegated_user = get_setting('GMAIL_DELEGATED_USER')
        self.sender_email = get_setting('GMAIL_SENDER_EMAIL') or self.delegated_user
        self.service_account_info = get_setting('GMAIL_SERVICE_ACCOUNT_INFO')
        self.service_account_file = get_setting('GMAIL_SERVICE_ACCOUNT_FILE')

    def _load_service_account_credentials(self):
        if Credentials is None:
            raise RuntimeError(
                'Dependências do Google API não instaladas. Adicione google-api-python-client e google-auth.'
            )

        credentials = None

        if isinstance(self.service_account_info, dict):
            credentials = Credentials.from_service_account_info(
                self.service_account_info,
                scopes=GMAIL_SCOPES,
            )
        elif isinstance(self.service_account_info, str) and self.service_account_info.strip():
            credentials = Credentials.from_service_account_info(
                json.loads(self.service_account_info),
                scopes=GMAIL_SCOPES,
            )
        elif self.service_account_file:
            credentials = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=GMAIL_SCOPES,
            )
        else:
            raise RuntimeError(
                'Credenciais da Gmail API não configuradas. Informe GMAIL_SERVICE_ACCOUNT_INFO '
                'ou GMAIL_SERVICE_ACCOUNT_FILE.'
            )

        if not self.delegated_user:
            raise RuntimeError(
                'GMAIL_DELEGATED_USER não configurado. Para Gmail API com service account, '
                'é necessário informar o usuário Workspace a ser delegado.'
            )

        return credentials.with_subject(self.delegated_user)

    def _build_service(self):
        credentials = self._load_service_account_credentials()
        return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

    # ------------------------------------------------------------------
    # Logo helper
    # ------------------------------------------------------------------

    def _load_logo_bytes(self) -> bytes | None:
        """Retorna os bytes do logotipo ou None se o arquivo não existir."""
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, 'rb') as f:
                return f.read()
        return None

    # ------------------------------------------------------------------
    # Envio interno
    # ------------------------------------------------------------------

    def _send_raw(self, mime_msg) -> bool:
        """Serializa e envia uma mensagem MIME via Gmail API."""
        if not self.sender_email:
            raise RuntimeError('GMAIL_SENDER_EMAIL ou GMAIL_DELEGATED_USER não configurado.')
        try:
            service = self._build_service()
            raw_message = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            LOGGER.info('Email enviado para %s', mime_msg['to'])
            return True
        except RefreshError as e:
            error_text = str(e)
            if 'unauthorized_client' in error_text.lower():
                raise RuntimeError(
                    'Google API retornou unauthorized_client. Isso normalmente indica que a service account '
                    'não está autorizada para Domain-Wide Delegation no Google Workspace, que o escopo '
                    'https://www.googleapis.com/auth/gmail.send não foi autorizado no Admin Console, ou que '
                    'o usuário delegado não pertence ao domínio Workspace autorizado.'
                ) from e
            raise RuntimeError(f'Falha de autenticação na Google API: {e}') from e
        except Exception as e:
            LOGGER.exception('Erro inesperado ao enviar e-mail para %s', mime_msg.get('to', ''))
            raise RuntimeError(f'Erro inesperado ao enviar e-mail: {e}') from e

    def _build_mime_com_logo(self, destino: str, assunto: str, html_body: str) -> MIMEMultipart:
        """
        Constrói um MIMEMultipart('related') com o logotipo do Oráculo Analista
        embutido como imagem inline (CID: oraculo_logo).
        O HTML deve referenciar a imagem como: <img src="cid:oraculo_logo" ...>
        """
        outer = MIMEMultipart('related')
        outer['to'] = destino
        outer['from'] = self.sender_email
        outer['subject'] = assunto

        alternative = MIMEMultipart('alternative')
        alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
        outer.attach(alternative)

        logo_bytes = self._load_logo_bytes()
        if logo_bytes:
            img = MIMEImage(logo_bytes, _subtype='png')
            img.add_header('Content-ID', '<oraculo_logo>')
            img.add_header('Content-Disposition', 'inline', filename='logo.png')
            outer.attach(img)

        return outer

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> bool:
        """Envia um e-mail HTML simples (sem imagem embutida)."""
        if not self.sender_email:
            raise RuntimeError('GMAIL_SENDER_EMAIL ou GMAIL_DELEGATED_USER não configurado.')

        msg = MIMEText(mensagem, 'html', 'utf-8')
        msg['to'] = destino
        msg['from'] = self.sender_email
        msg['subject'] = assunto
        return self._send_raw(msg)

    def enviar_boas_vindas(
        self,
        nome: str,
        email: str,
        whatsapp: str,
        cargo: str = 'Cliente',
    ) -> bool:
        """
        Envia um e-mail de boas-vindas rico ao novo usuário com o logotipo
        do Oráculo Analista centralizado e os dados do cadastro.
        """
        assunto = '🎉 Bem-vindo(a) ao Oráculo Analista!'
        data_cadastro = datetime.now().strftime('%d/%m/%Y às %H:%M')
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background-color:#0d0d1a;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d1a;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(160deg,#1a1a2e 0%,#16213e 100%);
                      border-radius:16px;overflow:hidden;
                      border:1px solid #3a1f6e;">

          <!-- Logo + título -->
          <tr>
            <td align="center" style="padding:36px 32px 20px;">
              <img src="cid:oraculo_logo" alt="Oráculo Analista"
                   width="110" height="110"
                   style="border-radius:50%;border:3px solid #7c3aed;display:block;margin:0 auto 20px;"/>
              <h1 style="margin:0;font-size:28px;font-weight:700;
                         background:linear-gradient(90deg,#a855f7,#ffffff);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Bem-vindo(a) ao Oráculo Analista!
              </h1>
              <p style="margin:10px 0 0;font-size:15px;color:#b0aac8;">
                Sua jornada de inteligência analítica começa agora.
              </p>
            </td>
          </tr>

          <!-- Saudação -->
          <tr>
            <td style="padding:0 32px 16px;">
              <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
                Olá, <strong style="color:#a855f7;">{nome}</strong>! 👋<br/>
                Estamos muito felizes em tê-lo(a) como parte da nossa comunidade.
                O <strong>Oráculo Analista</strong> foi criado para transformar
                dados complexos em decisões estratégicas de alto impacto — e agora
                essa ferramenta está nas suas mãos.
              </p>
            </td>
          </tr>

          <!-- Dados do cadastro -->
          <tr>
            <td style="padding:0 32px 24px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#0f0f2a;border-radius:10px;
                            border:1px solid #3a1f6e;overflow:hidden;">
                <tr>
                  <td colspan="2" style="padding:14px 20px;
                      background:linear-gradient(90deg,#4c1d95,#1e3a8a);
                      font-size:13px;font-weight:700;
                      text-transform:uppercase;letter-spacing:1px;color:#e9d5ff;">
                    📋 Seus Dados de Cadastro
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;width:40%;">Nome</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{nome}</td>
                </tr>
                <tr style="background:#13132b;">
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">E-mail</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{email}</td>
                </tr>
                <tr>
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">WhatsApp</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{whatsapp}</td>
                </tr>
                <tr style="background:#13132b;">
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">Perfil</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{cargo}</td>
                </tr>
                <tr>
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">Cadastro em</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{data_cadastro}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- O que é o Oráculo Analista -->
          <tr>
            <td style="padding:0 32px 24px;">
              <h2 style="margin:0 0 12px;font-size:18px;color:#c084fc;">
                🤖 O que é o Oráculo Analista?
              </h2>
              <p style="margin:0;font-size:14px;line-height:1.7;color:#c4b8de;">
                O Oráculo Analista é uma plataforma de <strong>inteligência artificial avançada</strong>
                projetada para empresários, diretores e líderes estratégicos que precisam transformar
                grandes volumes de dados em <strong>insights acionáveis</strong> — de forma rápida,
                precisa e sem precisar ser técnico.
              </p>
            </td>
          </tr>

          <!-- Benefícios -->
          <tr>
            <td style="padding:0 32px 24px;">
              <h2 style="margin:0 0 14px;font-size:18px;color:#c084fc;">✨ O que você pode fazer</h2>
              <table width="100%" cellpadding="0" cellspacing="8">
                <tr>
                  <td style="padding:10px 14px;background:#1a103a;border-radius:8px;
                             border-left:3px solid #7c3aed;font-size:14px;color:#ddd6fe;">
                    📊 <strong>Análise de documentos e bancos de dados</strong> em segundos
                  </td>
                </tr>
                <tr><td style="height:6px;"></td></tr>
                <tr>
                  <td style="padding:10px 14px;background:#1a103a;border-radius:8px;
                             border-left:3px solid #2563eb;font-size:14px;color:#ddd6fe;">
                    🎯 <strong>Decisões estratégicas</strong> baseadas em dados concretos e confiáveis
                  </td>
                </tr>
                <tr><td style="height:6px;"></td></tr>
                <tr>
                  <td style="padding:10px 14px;background:#1a103a;border-radius:8px;
                             border-left:3px solid #0891b2;font-size:14px;color:#ddd6fe;">
                    ⚡ <strong>Respostas instantâneas</strong> a perguntas complexas sobre seus dados
                  </td>
                </tr>
                <tr><td style="height:6px;"></td></tr>
                <tr>
                  <td style="padding:10px 14px;background:#1a103a;border-radius:8px;
                             border-left:3px solid #059669;font-size:14px;color:#ddd6fe;">
                    🚀 <strong>Vantagem competitiva real</strong> para crescer com segurança
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Próximo passo -->
          <tr>
            <td style="padding:0 32px 32px;" align="center">
              <p style="font-size:14px;color:#b0aac8;margin:0 0 18px;">
                O próximo passo é verificar sua conta com o código que enviaremos em seguida.
                Após a verificação você terá acesso completo à plataforma.
              </p>
              <p style="margin:0;font-size:13px;color:#6b7280;">
                Se tiver dúvidas, responda este e-mail ou entre em contato pelo WhatsApp.
              </p>
            </td>
          </tr>

          <!-- Rodapé -->
          <tr>
            <td style="padding:20px 32px;background:#0a0a1a;border-top:1px solid #2d1b69;" align="center">
              <p style="margin:0;font-size:12px;color:#4b5563;">
                © {datetime.now().year} Oráculo Analista — Desenvolvido com ❤️ por Oráculos AI<br/>
                Este e-mail foi enviado automaticamente. Por favor, não responda diretamente.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        mime_msg = self._build_mime_com_logo(email, assunto, html)
        return self._send_raw(mime_msg)

    def enviar_verificacao(self, nome: str, email: str, codigo: str) -> bool:
        """
        Envia o e-mail de verificação de conta com o código de ativação,
        logotipo centralizado e template estilizado.
        """
        assunto = '🔐 Código de Verificação — Oráculo Analista'
        primeiro_nome = nome.split()[0] if nome else nome
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background-color:#0d0d1a;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d1a;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(160deg,#1a1a2e 0%,#16213e 100%);
                      border-radius:16px;overflow:hidden;
                      border:1px solid #3a1f6e;">

          <!-- Logo + título -->
          <tr>
            <td align="center" style="padding:36px 32px 20px;">
              <img src="cid:oraculo_logo" alt="Oráculo Analista"
                   width="110" height="110"
                   style="border-radius:50%;border:3px solid #7c3aed;display:block;margin:0 auto 20px;"/>
              <h1 style="margin:0;font-size:26px;font-weight:700;
                         background:linear-gradient(90deg,#a855f7,#ffffff);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Verifique sua conta
              </h1>
              <p style="margin:10px 0 0;font-size:15px;color:#b0aac8;">
                Oráculo Analista — Ativação de Conta
              </p>
            </td>
          </tr>

          <!-- Texto -->
          <tr>
            <td style="padding:0 32px 20px;">
              <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
                Olá, <strong style="color:#a855f7;">{primeiro_nome}</strong>! 👋<br/>
                Para ativar sua conta e ter acesso completo à plataforma,
                utilize o código de verificação abaixo:
              </p>
            </td>
          </tr>

          <!-- Código de verificação em destaque -->
          <tr>
            <td align="center" style="padding:0 32px 28px;">
              <table cellpadding="0" cellspacing="0"
                     style="background:linear-gradient(135deg,#4c1d95,#1e3a8a);
                            border-radius:12px;overflow:hidden;">
                <tr>
                  <td style="padding:10px 24px 4px;" align="center">
                    <p style="margin:0;font-size:12px;font-weight:700;letter-spacing:2px;
                               text-transform:uppercase;color:#c4b5fd;">
                      Seu Código de Verificação
                    </p>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding:8px 48px 16px;">
                    <span style="font-size:44px;font-weight:900;letter-spacing:12px;
                                 color:#ffffff;font-family:'Courier New',monospace;">
                      {codigo}
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Instruções -->
          <tr>
            <td style="padding:0 32px 24px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#1a103a;border-radius:10px;
                            border:1px solid #3730a3;">
                <tr>
                  <td style="padding:16px 20px;">
                    <p style="margin:0 0 8px;font-size:14px;font-weight:700;color:#c4b5fd;">
                      ⚠️ Informações importantes:
                    </p>
                    <ul style="margin:0;padding-left:20px;font-size:14px;
                               line-height:1.8;color:#b0aac8;">
                      <li>Insira este código na tela de verificação do Oráculo Analista.</li>
                      <li>O código é <strong>válido para uso único</strong>.</li>
                      <li>Se você não solicitou este código, ignore este e-mail.</li>
                    </ul>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Segurança -->
          <tr>
            <td style="padding:0 32px 32px;" align="center">
              <p style="font-size:13px;color:#6b7280;margin:0;">
                🔒 Por segurança, nunca compartilhe este código com ninguém.
              </p>
            </td>
          </tr>

          <!-- Rodapé -->
          <tr>
            <td style="padding:20px 32px;background:#0a0a1a;border-top:1px solid #2d1b69;" align="center">
              <p style="margin:0;font-size:12px;color:#4b5563;">
                © {datetime.now().year} Oráculo Analista — Desenvolvido com ❤️ por Oráculos AI<br/>
                Este e-mail foi enviado automaticamente. Por favor, não responda diretamente.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        mime_msg = self._build_mime_com_logo(email, assunto, html)
        return self._send_raw(mime_msg)

    def enviar_confirmacao_agendamento(self, nome, email, data, hora):
        assunto = 'Confirmação de Agendamento - Oráculo Analista'
        mensagem = f"""
        <h3>Olá {nome},</h3>
        <p>Seu agendamento foi confirmado para <strong>{data}</strong> às <strong>{hora}</strong>.</p>
        <p>Nos vemos em breve!</p>
        """
        self.enviar_email(email, assunto, mensagem)

    def enviar_confirmacao_pagamento(self, nome, email, plano):
        assunto = 'Pagamento Confirmado - Oráculo Analista'
        mensagem = f"""
        <h3>Olá {nome},</h3>
        <p>Seu pagamento do plano <strong>{plano}</strong> foi confirmado com sucesso.</p>
        <p>Você já pode acessar o Oráculo Analista com todos os recursos liberados.</p>
        """
        self.enviar_email(email, assunto, mensagem)


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
        LOGGER.info('Mensagem enviada para %s: %s', numero, mensagem)

    def confirmar_pagamento_upgrade(self, nome, numero, plano):
        mensagem = f'Olá {nome}, seu pagamento do plano {plano} foi confirmado. Acesso liberado ao Oráculo Analista.'
        self.enviar_mensagem(numero, mensagem)

    def confirmar_agendamento(self, nome, numero, data, hora):
        mensagem = f'Olá {nome}, seu agendamento foi confirmado para {data} às {hora}. Estamos esperando você!'
        self.enviar_mensagem(numero, mensagem)
