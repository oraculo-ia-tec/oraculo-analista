# ============================================================
# tests/test_helpers.py — testes unitários de src/utils/helpers
# ============================================================
import pytest
from src.utils.helpers import truncate, estimate_tokens, generate_id, now_iso


class TestTruncate:
    def test_texto_menor_que_limite_nao_trunca(self):
        assert truncate("ola", 100) == "ola"

    def test_texto_maior_que_limite_trunca(self):
        texto = "x" * 200
        resultado = truncate(texto, 100)
        assert len(resultado) < 200
        assert "truncado" in resultado

    def test_texto_exatamente_no_limite(self):
        texto = "a" * 50
        assert truncate(texto, 50) == texto

    def test_truncate_default_6000(self):
        texto = "z" * 7000
        resultado = truncate(texto)
        assert len(resultado) < 7000


class TestEstimateTokens:
    def test_retorna_inteiro_positivo(self):
        assert estimate_tokens("hello world") > 0

    def test_texto_vazio_retorna_1(self):
        assert estimate_tokens("") == 1

    def test_texto_maior_retorna_mais_tokens(self):
        curto = estimate_tokens("oi")
        longo = estimate_tokens("oi " * 1000)
        assert longo > curto

    def test_aproximacao_4_chars_por_token(self):
        # 400 chars ≈ 100 tokens
        tokens = estimate_tokens("a" * 400)
        assert tokens == 100


class TestGenerateId:
    def test_retorna_string(self):
        assert isinstance(generate_id(), str)

    def test_prefixo_incluido(self):
        assert generate_id("sess_").startswith("sess_")

    def test_ids_sao_unicos(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100


class TestNowIso:
    def test_retorna_string(self):
        assert isinstance(now_iso(), str)

    def test_formato_iso(self):
        ts = now_iso()
        assert "T" in ts
        assert "+" in ts or "Z" in ts or ts.endswith("+00:00")
