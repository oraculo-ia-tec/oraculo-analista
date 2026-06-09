# ============================================================
# src/tools/search_tool.py
# Tool de busca web (stub — expansível com SerpAPI / DuckDuckGo)
# ============================================================
from __future__ import annotations


class WebSearchTool:
    name        = "web_search"
    description = "Realiza buscas na web para complementar análises com informações atuais."
    permission  = "allow"

    def __call__(self, query: str = "", **kwargs) -> str:
        return f"Busca web para '{query}' não configurada neste ambiente. Use o contexto de arquivos carregados."
