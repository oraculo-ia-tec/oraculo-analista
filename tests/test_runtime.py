# ============================================================
# tests/test_runtime.py — testa Runtime com LLM mockado
# ============================================================
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def runtime(mock_secrets, mock_session_state):
    """Cria um Runtime com QueryEngine mockado."""
    with patch("src.runtime.QueryEngine") as MockQE:
        instance = MockQE.return_value
        instance.query.return_value = "Resposta mockada do LLM"
        from src.runtime import Runtime
        rt = Runtime(api_key="fake-key")
        rt.engine = instance
        return rt


class TestRuntime:
    def test_session_id_gerado(self, runtime):
        assert runtime.session_id.startswith("sess_")

    def test_run_retorna_string(self, runtime, mock_session_state):
        mock_session_state["messages"] = []
        mock_session_state["primeiro_nome"] = "William"
        resultado = runtime.run("Olá, tudo bem?")
        assert isinstance(resultado, str)
        assert len(resultado) > 0

    def test_run_chama_engine(self, runtime, mock_session_state):
        mock_session_state["messages"] = []
        mock_session_state["primeiro_nome"] = "William"
        runtime.run("teste")
        runtime.engine.query.assert_called_once()

    def test_reset_limpa_mensagens(self, runtime, mock_session_state):
        mock_session_state["messages"] = [{"role": "user", "content": "oi"}]
        runtime.reset_session()
        assert mock_session_state.get("messages") == []

    def test_cost_summary_retorna_dict(self, runtime):
        s = runtime.get_cost_summary()
        assert isinstance(s, dict)
        assert "cost_usd" in s

    def test_tools_registradas(self, runtime):
        nomes = list(runtime.tools._registry.keys())
        assert "file_read" in nomes or len(nomes) >= 1
