# ============================================================
# src/tools/base.py
# Interface base que toda tool deve implementar
# ============================================================
from abc import ABC, abstractmethod


class BaseTool(ABC):
    name: str
    description: str
    permission: str = "allow"

    @abstractmethod
    def __call__(self, **kwargs) -> str:
        """Executa a tool e retorna string com o resultado."""
        ...
