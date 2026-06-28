# ============================================================
# tests/test_cost_hook.py — testes do CostHook
# ============================================================
import pytest
from src.hooks.cost_hook import CostHook


@pytest.fixture
def hook():
    return CostHook()


class TestCostHook:
    def test_estado_inicial_zerado(self, hook):
        s = hook.summary()
        assert s["calls"] == 0
        assert s["input_tokens"] == 0
        assert s["output_tokens"] == 0
        assert s["cost_usd"] == 0.0

    def test_on_request_incrementa_input(self, hook):
        hook.on_request("a" * 400)  # ≈ 100 tokens
        assert hook.summary()["input_tokens"] == 100
        assert hook.summary()["calls"] == 1

    def test_on_response_incrementa_output(self, hook):
        hook.on_response("b" * 400)
        assert hook.summary()["output_tokens"] == 100

    def test_add_acumula_tokens(self, hook):
        hook.add(prompt_tokens=500, completion_tokens=200)
        s = hook.summary()
        assert s["input_tokens"] == 500
        assert s["output_tokens"] == 200
        assert s["total_tokens"] == 700
        assert s["calls"] == 1

    def test_custo_calculado(self, hook):
        hook.add(prompt_tokens=1_000_000, completion_tokens=1_000_000)
        assert hook.cost_usd > 0

    def test_reset_zera_tudo(self, hook):
        hook.add(500, 200)
        hook.reset()
        s = hook.summary()
        assert s["input_tokens"] == 0
        assert s["output_tokens"] == 0
        assert s["calls"] == 0

    def test_multiplas_chamadas_acumulam(self, hook):
        hook.add(100, 50)
        hook.add(200, 100)
        assert hook.summary()["total_tokens"] == 450
