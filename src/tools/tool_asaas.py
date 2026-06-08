"""
Tool de integração com a API Asaas (pagamentos e cobranças).
Substitui as chamadas diretas em api_asaas.py com interface padronizada.
"""
import os
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolAsaas(BaseTool):
    name = "tool_asaas"
    description = (
        "Consulta informações de pagamentos e cobranças via API Asaas. "
        "Permite listar cobranças, verificar status de pagamento e "
        "obter relatório financeiro de um cliente. "
        "Use apenas quando o usuário solicitar informações financeiras explicitamente."
    )
    plan_required = "pro"  # apenas plano Pro ou superior

    @property
    def parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_charges", "get_charge", "list_customers", "get_balance"],
                    "description": "Ação a executar na API Asaas.",
                },
                "charge_id": {
                    "type": "string",
                    "description": "ID da cobrança (necessário para get_charge).",
                },
                "customer_id": {
                    "type": "string",
                    "description": "ID do cliente para filtrar cobranças.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de registros a retornar. Padrão: 10.",
                    "default": 10,
                },
            },
            "required": ["action"],
        }

    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        action = parameters.get("action", "")
        valid_actions = ["list_charges", "get_charge", "list_customers", "get_balance"]
        if action not in valid_actions:
            return False, f"Ação inválida: '{action}'. Use: {valid_actions}"
        if action == "get_charge" and not parameters.get("charge_id"):
            return False, "'charge_id' é obrigatório para a ação 'get_charge'."
        return True, ""

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        import requests

        api_key = os.getenv("ASAAS_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ASAAS_API_KEY não configurada. Defina no arquivo .env"
            )

        base_url = os.getenv("BASE_URL_ASAAS", "https://api-sandbox.asaas.com/v3")
        headers = {
            "access_token": api_key,
            "Content-Type": "application/json",
        }

        action = parameters["action"]
        limit = parameters.get("limit", 10)

        if action == "list_charges":
            params = {"limit": limit}
            if parameters.get("customer_id"):
                params["customer"] = parameters["customer_id"]
            resp = requests.get(f"{base_url}/payments", headers=headers, params=params)

        elif action == "get_charge":
            charge_id = parameters["charge_id"]
            resp = requests.get(f"{base_url}/payments/{charge_id}", headers=headers)

        elif action == "list_customers":
            resp = requests.get(
                f"{base_url}/customers",
                headers=headers,
                params={"limit": limit}
            )

        elif action == "get_balance":
            resp = requests.get(f"{base_url}/finance/balance", headers=headers)

        resp.raise_for_status()
        return resp.json()


ToolRegistry.register(ToolAsaas())
