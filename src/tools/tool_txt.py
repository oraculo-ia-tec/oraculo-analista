"""
Tool de leitura de arquivos de texto puro (.txt, .md, .csv texto).
"""
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolTxt(BaseTool):
    name = "tool_txt"
    description = (
        "Lê o conteúdo de arquivos de texto puro (.txt, .md). "
        "Use para acessar relatórios, notas ou qualquer documento em texto simples."
    )
    plan_required = "free"

    @property
    def parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Caminho para o arquivo de texto.",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Máximo de caracteres a retornar. Padrão: 50000.",
                    "default": 50000,
                },
            },
            "required": ["filepath"],
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        from pathlib import Path

        filepath = parameters["filepath"]
        max_chars = parameters.get("max_chars", 50000)

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        content = path.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > max_chars
        content = content[:max_chars]

        return {
            "filename": path.name,
            "content": content,
            "char_count": len(content),
            "truncated": truncated,
        }


ToolRegistry.register(ToolTxt())
