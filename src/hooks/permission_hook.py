"""
Permission Hook — controla acesso a tools por plano do usuário.
Tools premium são bloqueadas para o plano gratuito.
"""
from typing import Optional
from src.hooks.base import BaseHook
from src.types.base import ToolCall, ToolResult


# Mapeamento de tools por plano mínimo necessário
TOOL_PERMISSIONS: dict[str, list[str]] = {
    "free": [
        "tool_pdf",
        "tool_txt",
        "tool_calculator",
    ],
    "pro": [
        "tool_pdf",
        "tool_excel",
        "tool_txt",
        "tool_calculator",
        "tool_web_search",
        "tool_chart_generator",
        "tool_export_pdf",
    ],
    "enterprise": "*",  # Todas as tools
}

PLAN_HIERARCHY = {"free": 0, "pro": 1, "enterprise": 2}


class PermissionHook(BaseHook):
    """
    Bloqueia tools não permitidas para o plano do usuário.
    Retorna mensagem amigável com sugestão de upgrade.
    """

    def __init__(self, user_plan: str):
        self.user_plan = user_plan

    def before_tool(self, tool_call: ToolCall) -> Optional[ToolResult]:
        allowed = TOOL_PERMISSIONS.get(self.user_plan, [])

        # Enterprise tem acesso total
        if allowed == "*":
            return None

        if tool_call.tool_name not in allowed:
            plan_label = {"free": "gratuito", "pro": "Pro"}.get(self.user_plan, self.user_plan)
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                error=(
                    f"🔒 Esta funcionalidade não está disponível no plano {plan_label}. "
                    f"Faça upgrade para o plano Pro para acessar "
                    f"`{tool_call.tool_name}` e muito mais."
                ),
            )

        return None

    def after_tool(self, tool_call: ToolCall, result: ToolResult) -> ToolResult:
        return result
