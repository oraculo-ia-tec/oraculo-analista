"""
Tool de envio de e-mail via SMTP Hostinger.
Usa as variáveis de ambiente definidas no .env do projeto.
Nenhuma credencial hardcoded neste arquivo.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolEmail(BaseTool):
    name = "tool_email"
    description = (
        "Envia um e-mail para um destinatário via servidor SMTP Hostinger. "
        "Use quando o usuário solicitar envio de relatório, "
        "resumo de análise ou qualquer comunicação por e-mail. "
        "SEMPRE peça confirmação explícita do usuário antes de enviar."
    )
    plan_required = "pro"  # apenas plano Pro ou superior

    @property
    def parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Endereço de e-mail do destinatário.",
                },
                "subject": {
                    "type": "string",
                    "description": "Assunto do e-mail.",
                },
                "body": {
                    "type": "string",
                    "description": "Corpo do e-mail em texto puro ou HTML.",
                },
                "is_html": {
                    "type": "boolean",
                    "description": "Se True, o corpo será enviado como HTML. Padrão: False.",
                    "default": False,
                },
            },
            "required": ["to", "subject", "body"],
        }

    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        import re
        to = parameters.get("to", "")
        subject = parameters.get("subject", "")
        body = parameters.get("body", "")

        if not to or not re.match(r"[^@]+@[^@]+\.[^@]+", to):
            return False, f"E-mail inválido: '{to}'"
        if not subject.strip():
            return False, "Assunto não pode ser vazio."
        if not body.strip():
            return False, "Corpo do e-mail não pode ser vazio."
        return True, ""

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        # --- Leitura das credenciais do .env (nunca hardcoded) ---
        host = os.getenv("EMAIL_HOST", "smtp.hostinger.com")
        port = int(os.getenv("EMAIL_PORT", "587"))
        username = os.getenv("EMAIL_USERNAME", "")
        password = os.getenv("EMAIL_PASSWORD", "")
        use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        remetente = os.getenv("EMAIL_REMETENTE", username)

        if not username or not password:
            raise EnvironmentError(
                "Credenciais de e-mail não configuradas. "
                "Defina EMAIL_USERNAME e EMAIL_PASSWORD no arquivo .env"
            )

        to = parameters["to"]
        subject = parameters["subject"]
        body = parameters["body"]
        is_html = parameters.get("is_html", False)

        # --- Monta a mensagem MIME ---
        msg = MIMEMultipart("alternative")
        msg["From"] = remetente
        msg["To"] = to
        msg["Subject"] = subject

        mime_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, mime_type, "utf-8"))

        # --- Envia via SMTP com STARTTLS ---
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            server.login(username, password)
            server.sendmail(remetente, [to], msg.as_string())

        return {
            "status": "enviado",
            "from": remetente,
            "to": to,
            "subject": subject,
            "host": host,
            "port": port,
        }


ToolRegistry.register(ToolEmail())
