"""
Testes automatizados — CostTracker

Cobre:
  - Registro de tokens por modelo
  - Cálculo de custo em USD e BRL
  - Acumulação entre múltiplas chamadas
  - Reset de sessão
"""
import pytest
from src.cost_tracker import CostTracker


class TestCostTracker:
    def setup_method(self):
        self.tracker = CostTracker()

    def test_inicia_zerado(self):
        assert self.tracker.total_tokens == 0
        assert self.tracker.total_cost_usd == 0.0
        assert self.tracker.total_cost_brl == 0.0

    def test_registra_tokens(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=1000, output_tokens=500)
        assert self.tracker.total_tokens == 1500

    def test_custo_usd_positivo(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=10000, output_tokens=5000)
        assert self.tracker.total_cost_usd > 0

    def test_custo_brl_maior_que_usd(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=10000, output_tokens=5000)
        assert self.tracker.total_cost_brl > self.tracker.total_cost_usd

    def test_acumula_multiplas_chamadas(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=500, output_tokens=500)
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=500, output_tokens=500)
        assert self.tracker.total_tokens == 2000

    def test_summary_retorna_dict(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=1000, output_tokens=1000)
        summary = self.tracker.summary()
        assert isinstance(summary, dict)
        assert "total_tokens" in summary
        assert "cost_usd" in summary
        assert "cost_brl" in summary

    def test_reset(self):
        self.tracker.record("llama-3.3-70b-versatile", input_tokens=1000, output_tokens=1000)
        self.tracker.reset()
        assert self.tracker.total_tokens == 0
        assert self.tracker.total_cost_usd == 0.0

    def test_modelo_desconhecido_nao_quebra(self):
        # Modelos sem tabela de preço devem usar custo zero sem exceção
        try:
            self.tracker.record("modelo-inexistente", input_tokens=1000, output_tokens=1000)
        except Exception as e:
            pytest.fail(f"CostTracker quebrou com modelo desconhecido: {e}")
