"""
Tool de leitura e extração de conteúdo de arquivos PDF.
Substitui a lógica de leitura de PDF dispersa em analista.py.
"""
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolPDF(BaseTool):
    name = "tool_pdf"
    description = (
        "Lê e extrai o texto completo de um arquivo PDF. "
        "Use quando o usuário fizer upload de um documento PDF "
        "ou quando precisar acessar o conteúdo de um PDF já carregado."
    )
    plan_required = "free"

    @property
    def parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Caminho completo para o arquivo PDF a ser lido.",
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Número máximo de páginas a extrair. Padrão: todas.",
                    "default": 0,
                },
            },
            "required": ["filepath"],
        }

    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        filepath = parameters.get("filepath", "")
        if not filepath:
            return False, "Parâmetro 'filepath' é obrigatório."
        if not filepath.lower().endswith(".pdf"):
            return False, f"Arquivo deve ser um PDF. Recebido: {filepath}"
        return True, ""

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        import pypdf
        from pathlib import Path

        filepath = parameters["filepath"]
        max_pages = parameters.get("max_pages", 0)

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        text_pages = []
        with open(filepath, "rb") as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            pages_to_read = total_pages if max_pages == 0 else min(max_pages, total_pages)

            for i in range(pages_to_read):
                page_text = reader.pages[i].extract_text() or ""
                text_pages.append(f"--- Página {i + 1} ---\n{page_text}")

        full_text = "\n\n".join(text_pages)
        return {
            "filename": path.name,
            "total_pages": total_pages,
            "pages_read": pages_to_read,
            "content": full_text,
            "char_count": len(full_text),
        }


# Auto-registro no ToolRegistry ao importar
ToolRegistry.register(ToolPDF())
