# ============================================================
# src/memory/session_memory.py
# Memória de sessão — extrai e resume tópicos da conversa
# ============================================================
from __future__ import annotations

import streamlit as st

from ..constants.settings import MAX_HISTORY_MESSAGES


class SessionMemory:
    """
    Mantém um resumo contínuo dos tópicos abordados na sessão.
    Não armazena mensagens completas — apenas metadados semânticos.
    """

    _KEY = "_session_memory"

    @classmethod
    def _get(cls) -> dict:
        if cls._KEY not in st.session_state:
            st.session_state[cls._KEY] = {
                "topics":       [],   # tópicos discutidos
                "files_analisados": [],  # nomes dos arquivos analisados
                "kpis_citados":  [],  # KPIs mencionados
                "turno":         0,
            }
        return st.session_state[cls._KEY]

    @classmethod
    def registrar_turno(cls, user_input: str, response: str) -> None:
        """Extrai metadados do turno e salva na memória."""
        mem = cls._get()
        mem["turno"] += 1

        # Detecta tópicos simples por palavras-chave
        topicos_detectados = cls._detectar_topicos(user_input)
        for t in topicos_detectados:
            if t not in mem["topics"]:
                mem["topics"].append(t)

        # Mantém lista compacta
        mem["topics"] = mem["topics"][-10:]

    @classmethod
    def registrar_arquivo(cls, nome: str) -> None:
        mem = cls._get()
        if nome not in mem["files_analisados"]:
            mem["files_analisados"].append(nome)

    @classmethod
    def to_prompt_str(cls) -> str:
        """Formata a memória para injeção no system prompt."""
        mem = cls._get()
        if mem["turno"] == 0:
            return ""

        linhas = [f"- Turno atual: {mem['turno']}"]

        if mem["topics"]:
            linhas.append("- Tópicos discutidos: " + ", ".join(mem["topics"]))

        if mem["files_analisados"]:
            linhas.append("- Arquivos analisados: " + ", ".join(mem["files_analisados"]))

        return "\n".join(linhas)

    @classmethod
    def reset(cls) -> None:
        st.session_state.pop(cls._KEY, None)

    # ── detecção de tópicos ──
    _TOPICO_MAP = {
        "faturamento":  ["faturamento", "receita", "vendas", "revenue"],
        "custo":        ["custo", "despesa", "gasto", "cost"],
        "margem":       ["margem", "lucro", "rentabilidade", "margin"],
        "crescimento":  ["crescimento", "aumento", "cresceu", "subiu"],
        "queda":        ["queda", "reduziu", "caiu", "diminuiu"],
        "comparação":   ["comparar", "diferença", "versus", "vs"],
        "resumo":       ["resumo", "resumir", "síntese", "overview"],
        "projeção":     ["projeção", "forecast", "estimar", "prever"],
        "kpi":          ["kpi", "indicador", "métrica", "performance"],
        "excel":        ["excel", "planilha", "xlsx", "aba"],
        "pdf":          ["pdf", "documento", "relatório"],
    }

    @classmethod
    def _detectar_topicos(cls, texto: str) -> list[str]:
        texto_lower = texto.lower()
        return [
            topico
            for topico, palavras in cls._TOPICO_MAP.items()
            if any(p in texto_lower for p in palavras)
        ]
