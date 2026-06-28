# ============================================================
# tests/test_settings.py — garante que decouple nunca volte
# ============================================================
import ast
import os
import pytest


def coletar_arquivos_python(raiz: str = ".") -> list[str]:
    arquivos = []
    excluir = {"copia", ".venv", "venv", "__pycache__", ".git", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = [d for d in dirnames if d not in excluir]
        for f in filenames:
            if f.endswith(".py"):
                arquivos.append(os.path.join(dirpath, f))
    return arquivos


class TestSemDecouple:
    """Garante que nenhum arquivo .py do projeto importa python-decouple."""

    def test_nenhum_arquivo_importa_decouple(self):
        arquivos_com_decouple = []
        for caminho in coletar_arquivos_python():
            try:
                with open(caminho, encoding="utf-8") as f:
                    codigo = f.read()
                if "from decouple" in codigo or "import decouple" in codigo:
                    arquivos_com_decouple.append(caminho)
            except Exception:
                pass

        assert arquivos_com_decouple == [], (
            f"Arquivos com decouple encontrados:\n"
            + "\n".join(arquivos_com_decouple)
        )


class TestSettings:
    """Valida que as constantes críticas existem e têm valores corretos."""

    def test_constantes_existem(self):
        from src.constants.settings import (
            APP_NAME, DEFAULT_MODEL,
            MAX_TOKENS_FREE_PLAN, MAX_TOKENS_PRO_PLAN,
            MAX_CONTEXT_CHARS, COST_PER_1M_INPUT_TOKENS,
            COST_PER_1M_OUTPUT_TOKENS,
        )
        assert APP_NAME == "Oráculo Analista"
        assert MAX_TOKENS_FREE_PLAN == 4096
        assert MAX_TOKENS_PRO_PLAN  == 8192
        assert MAX_CONTEXT_CHARS    == 40_000
        assert COST_PER_1M_INPUT_TOKENS  > 0
        assert COST_PER_1M_OUTPUT_TOKENS > 0

    def test_modelo_default_definido(self):
        from src.constants.settings import DEFAULT_MODEL
        assert isinstance(DEFAULT_MODEL, str)
        assert len(DEFAULT_MODEL) > 0
