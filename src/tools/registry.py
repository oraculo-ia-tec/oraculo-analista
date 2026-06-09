# ============================================================
# src/tools/registry.py
# Registro central de tools (estilo Claude Code tools.py)
# ============================================================
from typing import Callable


class ToolRegistry:
    """
    Mantém o catálogo de tools disponíveis para o agente.

    Cada tool é registrada com:
        name        → identificador único
        description → descrita ao LLM no system prompt
        func        → callable que executa a tool
        permission  → chave de permissão (ver permissions.py)
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        permission: str = "allow",
    ) -> None:
        self._tools[name] = {
            "name":        name,
            "description": description,
            "func":        func,
            "permission":  permission,
        }

    def get(self, name: str) -> dict | None:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> str:
        """Executa uma tool pelo nome."""
        tool = self._tools.get(name)
        if not tool:
            return f"[ToolRegistry] Tool '{name}' não encontrada."
        try:
            result = tool["func"](**kwargs)
            return str(result)
        except Exception as exc:  # noqa: BLE001
            return f"[ToolRegistry] Erro ao executar '{name}': {exc}"

    def list_tools(self) -> list[dict]:
        """Retorna metadados de todas as tools (sem o callable)."""
        return [
            {"name": t["name"], "description": t["description"], "permission": t["permission"]}
            for t in self._tools.values()
        ]

    def describe_for_prompt(self) -> str:
        """Formata tools para injeção no system prompt."""
        lines = ["## Tools disponíveis"]
        for t in self.list_tools():
            lines.append(f"- **{t['name']}**: {t['description']}")
        return "\n".join(lines)
