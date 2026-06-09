# ============================================================
# src/tools/search_tool.py
# Tool de busca na web (stub — integração futura DuckDuckGo)
# ============================================================


class WebSearchTool:
    """
    Realiza buscas na web.
    Atualmente retorna um stub — pronto para integrar
    DuckDuckGo Search API ou SerpAPI.
    """

    name        = "web_search"
    description = "Busca informações atualizadas na web quando o contexto local não é suficiente."
    permission  = "web_search"

    def __call__(self, query: str) -> str:
        # TODO: integrar requests + DuckDuckGo Instant Answer API
        return (
            f"[web_search] Busca por '{query}' ainda não integrada nesta versão. "
            "Responda com base no seu conhecimento interno."
        )
