# ============================================================
# src/tools/registry.py
# Registro central de tools disponíveis para o agente
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ToolEntry:
    name:        str
    description: str
    func:        Callable
    permission:  str = "allow"


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolEntry] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        permission: str = "allow",
    ) -> None:
        self._tools[name] = ToolEntry(
            name=name,
            description=description,
            func=func,
            permission=permission,
        )

    def get(self, name: str) -> ToolEntry | None:
        return self._tools.get(name)

    def describe_for_prompt(self) -> str:
        if not self._tools:
            return ""
        lines = ["## Tools disponíveis:"]
        for t in self._tools.values():
            lines.append(f"- **{t.name}**: {t.description}")
        return "\n".join(lines)

    def all(self) -> list[ToolEntry]:
        return list(self._tools.values())
