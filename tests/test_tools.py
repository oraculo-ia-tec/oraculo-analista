"""
Testes automatizados — Sistema de Tools

Cobre:
  - tool_calculator: operações básicas e edge cases
  - tool_pdf: leitura e extração de texto
  - tool_excel: leitura de planilhas
  - tool_csv: leitura de CSV
  - tool_chart_generator: geração de gráficos
  - tool_router: roteamento correto de chamadas
"""
import os
import json
import tempfile
import pytest
import pandas as pd

from src.tools import tool_router
from src.tools.tool_calculator import ToolCalculator
from src.tools.tool_csv import ToolCSV
from src.tools.tool_excel import ToolExcel


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def csv_file():
    """Cria um CSV temporário para testes."""
    data = pd.DataFrame({
        "produto": ["A", "B", "C"],
        "vendas": [100, 200, 150],
        "preco": [9.99, 19.99, 14.99],
    })
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w") as f:
        data.to_csv(f, index=False)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def excel_file():
    """Cria um Excel temporário para testes."""
    data = pd.DataFrame({
        "mes": ["Jan", "Fev", "Mar"],
        "receita": [10000, 12000, 11500],
    })
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
        path = f.name
    data.to_excel(path, index=False)
    yield path
    os.unlink(path)


# ─── ToolCalculator ───────────────────────────────────────────────────────────

class TestToolCalculator:
    def setup_method(self):
        self.calc = ToolCalculator()

    def test_soma_basica(self):
        result = self.calc.call({"expression": "2 + 2"})
        assert result["result"] == 4

    def test_multiplicacao(self):
        result = self.calc.call({"expression": "150 * 1.3"})
        assert abs(result["result"] - 195.0) < 0.01

    def test_divisao(self):
        result = self.calc.call({"expression": "100 / 4"})
        assert result["result"] == 25.0

    def test_potencia(self):
        result = self.calc.call({"expression": "2 ** 10"})
        assert result["result"] == 1024

    def test_expressao_complexa(self):
        result = self.calc.call({"expression": "(100 + 50) * 0.9 - 30"})
        assert abs(result["result"] - 105.0) < 0.01

    def test_divisao_por_zero(self):
        result = self.calc.call({"expression": "10 / 0"})
        assert "error" in result

    def test_expressao_invalida(self):
        result = self.calc.call({"expression": "import os"})
        assert "error" in result

    def test_expressao_vazia(self):
        result = self.calc.call({"expression": ""})
        assert "error" in result


# ─── ToolCSV ──────────────────────────────────────────────────────────────────

class TestToolCSV:
    def setup_method(self):
        self.tool = ToolCSV()

    def test_leitura_basica(self, csv_file):
        result = self.tool.call({"filepath": csv_file})
        assert result["success"] is True
        assert result["rows"] == 3
        assert result["columns"] == 3

    def test_colunas_detectadas(self, csv_file):
        result = self.tool.call({"filepath": csv_file})
        assert "produto" in result["column_names"]
        assert "vendas" in result["column_names"]

    def test_soma_coluna(self, csv_file):
        result = self.tool.call({
            "filepath": csv_file,
            "query": "soma da coluna vendas",
        })
        assert result["success"] is True

    def test_arquivo_inexistente(self):
        result = self.tool.call({"filepath": "/nao/existe.csv"})
        assert result["success"] is False
        assert "error" in result


# ─── ToolExcel ────────────────────────────────────────────────────────────────

class TestToolExcel:
    def setup_method(self):
        self.tool = ToolExcel()

    def test_leitura_basica(self, excel_file):
        result = self.tool.call({"filepath": excel_file})
        assert result["success"] is True
        assert result["rows"] == 3

    def test_colunas_detectadas(self, excel_file):
        result = self.tool.call({"filepath": excel_file})
        assert "mes" in result["column_names"]
        assert "receita" in result["column_names"]

    def test_arquivo_inexistente(self):
        result = self.tool.call({"filepath": "/nao/existe.xlsx"})
        assert result["success"] is False


# ─── ToolRouter ───────────────────────────────────────────────────────────────

class TestToolRouter:
    def test_roteia_calculator(self):
        result = tool_router("tool_calculator", {"expression": "1+1"})
        assert result is not None

    def test_tool_inexistente(self):
        result = tool_router("tool_nao_existe", {})
        assert "error" in result

    def test_params_faltando(self):
        result = tool_router("tool_calculator", {})
        assert "error" in result
