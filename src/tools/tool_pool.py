"""
Pool de execução de tools.
Rota as tool_calls do LLM para a tool correta no ToolRegistry.
"""
from typing import List

from src.types.base import ToolCall, ToolResult, ToolStatus
from src.tools.base import ToolRegistry


class ToolPool:
    """
    Camada de despacho entre o query_engine e as tools.
    Responsabilidades:
      - Localizar a tool certa no registry
      - Executar com timeout implícito (via BaseTool.execute)
      - Retornar ToolResult padronizado em qualquer caso
    """

    def dispatch(self, tool_call: ToolCall) -> ToolResult:
        """
        Executa uma única tool_call.
        Retorna ToolResult com status ERROR se a tool não for encontrada.
        """
        tool = ToolRegistry.get(tool_call.tool_name)

        if tool is None:
            return ToolResult(
                tool_id=tool_call.tool_id,
                tool_name=tool_call.tool_name,
                status=ToolStatus.ERROR,
                error=(
                    f"Tool '{tool_call.tool_name}' não encontrada no registry. "
                    f"Tools disponíveis: {ToolRegistry.list_names()}"
                ),
            )

        return tool.execute(tool_call)

    def dispatch_many(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Executa uma lista de tool_calls em sequência.
        Retorna lista de ToolResult na mesma ordem.
        """
        return [self.dispatch(tc) for tc in tool_calls]
