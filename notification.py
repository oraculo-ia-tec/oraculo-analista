import base64
import json
import logging
import os
from datetime import datetime
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

    def enviar_email(self, destino, assunto, mensagem):
        if not self.sender_email:
            raise RuntimeError('GMAIL_SENDER_EMAIL ou GMAIL_DELEGATED_USER não configurado.')

        try:
            service = self._build_service()

            msg = MIMEText(mensagem, 'html', 'utf-8')
            msg['to'] = destino
            msg['from'] = self.sender_email
            msg['subject'] = assunto

            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            body = {'raw': raw_message}

            service.users().messages().send(userId='me', body=body).execute()
            LOGGER.info('Email enviado para %s', destino)
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
            LOGGER.exception('Erro inesperado ao enviar e-mail para %s', destino)
            raise RuntimeError(f'Erro inesperado ao enviar e-mail para {destino}: {e}') from e

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
