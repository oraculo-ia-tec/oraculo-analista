# ============================================================
# src/tools/file_tools.py
# Tool de leitura de arquivos
# ============================================================
from __future__ import annotations


class FileReadTool:
    name        = "file_read"
    description = "Lê e extrai texto de arquivos carregados pelo usuário (PDF, XLSX, DOCX, TXT, JSON, XML, HTML)."
    permission  = "allow"

    def __call__(self, file_path: str = "", **kwargs) -> str:
        """No contexto Streamlit, o conteúdo já está em file_context. Retorna mensagem informativa."""
        return f"Arquivo '{file_path}' disponível no contexto da sessão."
