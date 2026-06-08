"""
Sistema de Hooks — Orá culo Analista v2.0

Hooks interceptam eventos ANTES e DEPOIS da execução de cada tool.
Permitem auditoria, bloqueio, logging e modificação de comportamento
sem alterar o código da tool em si.

Padrão Observer/Middleware inspirado no Claude Code.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from src.types.base import ToolCall, ToolResult


class BaseHook(ABC):
    """Interface base para todos os hooks."""

    @abstractmethod
    def before_tool(self, tool_call: ToolCall) -> Optional[ToolResult]:
        """
        Executado ANTES da tool.
        Retorne None para deixar a tool executar normalmente.
        Retorne um ToolResult para bloquear a execução (curto-circuito).
        """
        ...

    @abstractmethod
    def after_tool(self, tool_call: ToolCall, result: ToolResult) -> ToolResult:
        """
        Executado APÓS a tool.
        Pode modificar ou enriquecer o resultado.
        Deve retornar o resultado (modificado ou não).
        """
        ...


class HookChain:
    """
    Cadeia de hooks executados em sequência.
    Cada hook pode bloquear a execução ou modificar o resultado.
    """

    def __init__(self):
        self._hooks: list[BaseHook] = []

    def register(self, hook: BaseHook) -> None:
        self._hooks.append(hook)

    def run_before(self, tool_call: ToolCall) -> Optional[ToolResult]:
        """Executa todos os before_tool. Retorna bloqueio se algum bloquear."""
        for hook in self._hooks:
            result = hook.before_tool(tool_call)
            if result is not None:
                return result
        return None

    def run_after(self, tool_call: ToolCall, result: ToolResult) -> ToolResult:
        """Executa todos os after_tool em sequência."""
        for hook in self._hooks:
            result = hook.after_tool(tool_call, result)
        return result


# Instância global da cadeia de hooks
hook_chain = HookChain()
