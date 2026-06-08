"""
Tool de envio de e-mail via Gmail API OAuth2.
Substitui o envio_email_real.py com interface padronizada de tool.
"""
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolEmail(BaseTool):
    name = "tool_email"
    description = (
        "Envia um e-mail para um destinatário via Gmail. "
        "Use quando o usuário solicitar envio de relatório, "
        "resumo de análise ou qualquer comunicação por e-mail. "
        "SEMPRE peça confirmação do usuário antes de enviar."
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
        import base64
        import os
        from email.mime.text import MIMEText
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        to = parameters["to"]
        subject = parameters["subject"]
        body = parameters["body"]
        is_html = parameters.get("is_html", False)

        # Carrega credenciais do tokens.json (gerado por gerar_refresh_token_gmail.py)
        token_path = os.path.join(os.path.dirname(__file__), "..", "..", "tokens.json")
        if not os.path.exists(token_path):
            raise FileNotFoundError(
                "tokens.json não encontrado. "
                "Execute gerar_refresh_token_gmail.py primeiro."
            )

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("gmail", "v1", credentials=creds)

        # Monta a mensagem
        mime_type = "html" if is_html else "plain"
        message = MIMEText(body, mime_type)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "enviado",
            "message_id": result.get("id"),
            "to": to,
            "subject": subject,
        }


ToolRegistry.register(ToolEmail())
