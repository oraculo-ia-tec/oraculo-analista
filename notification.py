import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import AutoConfig

try:
    import streamlit as st
except Exception:
    st = None


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
config = AutoConfig()

LOGO_PATH = os.path.join(os.path.dirname(
    __file__), 'src', 'img', 'perfil-analista.png')


def get_setting(key: str, default=None):
    try:
        value = config(key, default=None)
        if value is not None:
            return value
    except Exception:
        pass

    value = os.getenv(key)
    if value is not None:
        return value

    if st is not None:
        try:
            if 'email' in st.secrets and key in st.secrets['email']:
                return st.secrets['email'][key]
            if key in st.secrets:
                value = st.secrets[key]
                if hasattr(value, 'to_dict'):
                    return value.to_dict()
                return value
        except Exception:
            pass

    return default


def _as_bool(value, default: bool = False) -> bool:
  if value is None:
    return default
  if isinstance(value, bool):
    return value
  return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


class Notificador:
    """
    Envia e-mails via servidor SMTP configurado em .env ou st.secrets.

    Variáveis esperadas:
    - EMAIL_HOST
    - EMAIL_PORT
    - EMAIL_USERNAME
    - EMAIL_PASSWORD
    - EMAIL_USE_TLS
    - EMAIL_USE_SSL
    - EMAIL_REMETENTE
    """

    def __init__(self):
        self.smtp_host = get_setting('EMAIL_HOST')
        self.smtp_port = int(get_setting('EMAIL_PORT', 0) or 0)
        self.smtp_username = get_setting('EMAIL_USERNAME')
        self.smtp_password = get_setting('EMAIL_PASSWORD')
        self.use_tls = _as_bool(get_setting('EMAIL_USE_TLS'), default=True)
        self.use_ssl = _as_bool(get_setting('EMAIL_USE_SSL'), default=False)
        self.sender_email = get_setting('EMAIL_REMETENTE')

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

    def _send_via_smtp(self, mime_msg) -> bool:
        """Envia uma mensagem MIME via servidor SMTP configurado."""
        if not all([self.smtp_host, self.smtp_port, self.smtp_username, self.smtp_password]):
            raise RuntimeError(
                'Configuração SMTP incompleta. Verifique EMAIL_HOST, EMAIL_PORT, '
                'EMAIL_USERNAME e EMAIL_PASSWORD.'
            )
        if self.use_ssl and self.use_tls:
            raise RuntimeError(
                'EMAIL_USE_TLS e EMAIL_USE_SSL não podem ser verdadeiros ao mesmo tempo.'
            )

        try:
            context = ssl.create_default_context()
            server_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
            with server_class(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                if self.use_tls and not self.use_ssl:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(mime_msg)
            LOGGER.info('Email enviado (SMTP) para %s', mime_msg['to'])
            return True
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                'Falha de autenticação SMTP. Verifique EMAIL_USERNAME e EMAIL_PASSWORD.'
            ) from e
        except Exception as e:
            LOGGER.exception(
                'Erro ao enviar e-mail via SMTP para %s', mime_msg.get('to', ''))
            raise RuntimeError(f'Erro ao enviar e-mail via SMTP: {e}') from e

    def _send_raw(self, mime_msg) -> bool:
        """Envia via SMTP."""
        if not self.sender_email:
            raise RuntimeError('EMAIL_REMETENTE não configurado.')
        return self._send_via_smtp(mime_msg)

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
            img.add_header('Content-Disposition',
                           'inline', filename='logo.png')
            outer.attach(img)

        return outer

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> bool:
        """Envia um e-mail HTML simples (sem imagem embutida)."""
        if not self.sender_email:
            raise RuntimeError('EMAIL_REMETENTE não configurado.')

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
              <h1 style="margin:0;font-size:28px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">
                <span style="color:#c084fc;">✨</span> Bem-vindo(a) ao Oráculo Analista!
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
              <h1 style="margin:0;font-size:26px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">
                <span style="color:#c084fc;">🔐</span> Verifique sua conta
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

    def enviar_recuperacao_senha(self, nome: str, email: str, link: str) -> bool:
        """Envia e-mail com o link de recuperação de senha."""
        assunto = '🔑 Recuperação de Senha — Oráculo Analista'
        primeiro_nome = nome.split()[0] if nome else 'usuário'
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background-color:#0d0d1a;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d1a;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:linear-gradient(160deg,#1a1a2e 0%,#16213e 100%);
                    border-radius:16px;overflow:hidden;border:1px solid #3a1f6e;">
        <tr><td align="center" style="padding:36px 32px 20px;">
          <img src="cid:oraculo_logo" alt="Oráculo Analista"
               width="110" height="110"
               style="border-radius:50%;border:3px solid #7c3aed;display:block;margin:0 auto 20px;"/>
          <h1 style="margin:0;font-size:26px;font-weight:800;color:#ffffff;">
            <span style="color:#c084fc;">🔑</span> Recuperação de Senha
          </h1>
          <p style="margin:10px 0 0;font-size:15px;color:#b0aac8;">
            Oráculo Analista — Redefinição de Acesso
          </p>
        </td></tr>
        <tr><td style="padding:0 32px 20px;">
          <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
            Olá, <strong style="color:#a855f7;">{primeiro_nome}</strong>! 👋<br/>
            Recebemos uma solicitação para redefinir a senha da sua conta.
            Clique no botão abaixo para criar uma nova senha:
          </p>
        </td></tr>
        <tr><td align="center" style="padding:8px 32px 28px;">
          <a href="{link}"
             style="display:inline-block;padding:14px 32px;
                    background:linear-gradient(135deg,#7c3aed,#4c1d95);
                    color:#ffffff;text-decoration:none;font-weight:700;
                    font-size:16px;border-radius:10px;letter-spacing:0.5px;">
            🔐 Redefinir Minha Senha
          </a>
        </td></tr>
        <tr><td style="padding:0 32px 24px;">
          <p style="font-size:13px;color:#8b85a8;line-height:1.6;">
            Se o botão não funcionar, copie e cole o link abaixo no seu navegador:<br/>
            <a href="{link}" style="color:#c084fc;word-break:break-all;">{link}</a>
          </p>
        </td></tr>
        <tr><td style="padding:0 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#1a103a;border-radius:10px;border:1px solid #3730a3;">
            <tr><td style="padding:16px 20px;">
              <p style="margin:0 0 8px;font-size:14px;font-weight:700;color:#c4b5fd;">
                ⚠️ Informações importantes:
              </p>
              <ul style="margin:0;padding-left:20px;font-size:14px;line-height:1.8;color:#b0aac8;">
                <li>Este link é <strong>válido por 60 minutos</strong>.</li>
                <li>O link só pode ser utilizado <strong>uma única vez</strong>.</li>
                <li>Se você não solicitou esta redefinição, ignore este e-mail.</li>
              </ul>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:0 32px 32px;" align="center">
          <p style="font-size:13px;color:#6b7280;margin:0;">
            🔒 Por segurança, nunca compartilhe este link com ninguém.
          </p>
        </td></tr>
        <tr><td style="padding:20px 32px;background:#0a0a1a;border-top:1px solid #2d1b69;" align="center">
          <p style="margin:0;font-size:12px;color:#4b5563;">
            © {datetime.now().year} Oráculo Analista — Desenvolvido com ❤️ por Oráculos AI
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>
"""
        mime_msg = self._build_mime_com_logo(email, assunto, html)
        return self._send_raw(mime_msg)

    def enviar_senha_alterada(self, nome: str, email: str) -> bool:
        """Confirma ao usuário que a senha foi alterada com sucesso."""
        assunto = '✅ Senha Alterada com Sucesso — Oráculo Analista'
        primeiro_nome = nome.split()[0] if nome else 'usuário'
        agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background-color:#0d0d1a;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d1a;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:linear-gradient(160deg,#1a1a2e 0%,#16213e 100%);
                    border-radius:16px;overflow:hidden;border:1px solid #166534;">
        <tr><td align="center" style="padding:36px 32px 20px;">
          <img src="cid:oraculo_logo" alt="Oráculo Analista"
               width="110" height="110"
               style="border-radius:50%;border:3px solid #22c55e;display:block;margin:0 auto 20px;"/>
          <h1 style="margin:0;font-size:26px;font-weight:800;color:#ffffff;">
            <span style="color:#22c55e;">✅</span> Senha Alterada com Sucesso
          </h1>
          <p style="margin:10px 0 0;font-size:15px;color:#b0aac8;">
            Oráculo Analista — Confirmação de Segurança
          </p>
        </td></tr>
        <tr><td style="padding:0 32px 20px;">
          <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
            Olá, <strong style="color:#22c55e;">{primeiro_nome}</strong>! 👋<br/>
            Confirmamos que a senha da sua conta foi <strong>alterada com sucesso</strong>
            em <strong>{agora}</strong>.
          </p>
          <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
            Você já pode acessar o Oráculo Analista normalmente utilizando
            sua nova senha.
          </p>
        </td></tr>
        <tr><td style="padding:0 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#0f1f12;border-radius:10px;border:1px solid #166534;">
            <tr><td style="padding:16px 20px;">
              <p style="margin:0 0 8px;font-size:14px;font-weight:700;color:#86efac;">
                🛡️ Não foi você?
              </p>
              <p style="margin:0;font-size:14px;line-height:1.6;color:#b0aac8;">
                Se você <strong>não realizou</strong> esta alteração, entre em contato
                imediatamente com nosso suporte para proteger sua conta.
              </p>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:20px 32px;background:#0a0a1a;border-top:1px solid #166534;" align="center">
          <p style="margin:0;font-size:12px;color:#4b5563;">
            © {datetime.now().year} Oráculo Analista — Desenvolvido com ❤️ por Oráculos AI
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>
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

    def enviar_notificacao_novo_usuario(
        self,
        nome_novo: str,
        email_novo: str,
        cargo: str,
        email_destino: str,
    ) -> bool:
        """Notifica o administrador/dev sobre um novo cadastro no sistema."""
        assunto = '🆕 Novo usuário cadastrado — Oráculo Analista'
        data_hora = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background-color:#0d0d1a;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d1a;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(160deg,#1a1a2e 0%,#16213e 100%);
                      border-radius:16px;overflow:hidden;border:1px solid #3a1f6e;">
          <tr>
            <td align="center" style="padding:36px 32px 20px;">
              <img src="cid:oraculo_logo" alt="Oráculo Analista"
                   width="90" height="90"
                   style="border-radius:50%;border:3px solid #7c3aed;display:block;margin:0 auto 16px;"/>
              <h1 style="margin:0;font-size:26px;font-weight:800;
                         color:#ffffff;letter-spacing:0.5px;">
                <span style="color:#c084fc;">🆕</span> Novo Cadastro Detectado
              </h1>
              <p style="margin:8px 0 0;font-size:13px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;">
                Oráculo Analista — Notificação Automática
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;">
              <p style="font-size:15px;color:#d0c8e8;">
                Um novo usuário acaba de se cadastrar na plataforma:
              </p>
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#0f0f2a;border-radius:10px;border:1px solid #3a1f6e;">
                <tr>
                  <td colspan="2" style="padding:12px 20px;
                      background:linear-gradient(90deg,#4c1d95,#1e3a8a);
                      font-size:12px;font-weight:700;text-transform:uppercase;
                      letter-spacing:1px;color:#e9d5ff;">
                    Dados do Novo Usuário
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;width:35%;">Nome</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{nome_novo}</td>
                </tr>
                <tr style="background:#13132b;">
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">E-mail</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{email_novo}</td>
                </tr>
                <tr>
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">Cargo</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{cargo}</td>
                </tr>
                <tr style="background:#13132b;">
                  <td style="padding:10px 20px;color:#9ca3af;font-size:14px;">Data/Hora</td>
                  <td style="padding:10px 20px;color:#f3f4f6;font-size:14px;font-weight:600;">{data_hora}</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 32px;" align="center">
              <p style="font-size:13px;color:#6b7280;margin:0;">
                Este e-mail foi gerado automaticamente pela automação do Oráculo Analista.
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
        mime_msg = self._build_mime_com_logo(email_destino, assunto, html)
        return self._send_raw(mime_msg)


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
