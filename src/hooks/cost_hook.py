"""
Cost Hook — monitora e limita o custo de tokens por sessão.
Bloqueio preventivo antes de tools que consomem muitos tokens.
"""
from typing import Optional
from src.hooks.base import BaseHook
from src.types.base import ToolCall, ToolResult
from src.constants.settings import MAX_TOKENS_FREE_PLAN, MAX_TOKENS_PRO_PLAN


class CostHook(BaseHook):
    """
    Bloqueia execução de tools quando o usuário está próximo do limite de tokens.
    Limites por plano:
      free:       50.000 tokens/sessão
      pro:       500.000 tokens/sessão
      enterprise: ilimitado
    """

    # Tools que consomem muitos tokens (bloqueadas próximo ao limite)
    HEAVY_TOOLS = {"tool_pdf", "tool_excel", "tool_web_search"}

    def __init__(self, session):
        self.session = session

    def before_tool(self, tool_call: ToolCall) -> Optional[ToolResult]:
        plan = self.session.user.plan
        tokens_used = self.session.total_tokens

        # Enterprise: sem limite
        if plan == "enterprise":
            return None

        limit = MAX_TOKENS_PRO_PLAN if plan == "pro" else MAX_TOKENS_FREE_PLAN
        usage_pct = tokens_used / limit if limit > 0 else 0

        # Bloqueia tools pesadas quando acima de 90% do limite
        if usage_pct >= 0.90 and tool_call.tool_name in self.HEAVY_TOOLS:
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                error=(
                    f"⚠️ Limite de uso próximo ({usage_pct:.0%}). "
                    f"Operações pesadas bloqueadas. "
                    f"Upgrade para o plano Pro para continuar."
                ),
            )

        # Bloqueia tudo quando acima de 100%
        if usage_pct >= 1.0:
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                error="🚫 Limite de tokens esgotado para esta sessão.",
            )

        return None

    def after_tool(self, tool_call: ToolCall, result: ToolResult) -> ToolResult:
        # Não modifica o resultado — apenas monitora
        return result
