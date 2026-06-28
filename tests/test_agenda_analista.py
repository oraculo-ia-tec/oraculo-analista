# ============================================================
# tests/test_agenda_analista.py — testes da classe AgendaAnalista
# ============================================================
import pytest
from agenda_analista import AgendaAnalista


@pytest.fixture
def agenda():
    return AgendaAnalista()


class TestDetectarIntencao:
    """Testa se a detecção de intenção de agendamento funciona."""

    @pytest.mark.parametrize("prompt", [
        "quero agendar uma reunião",
        "preciso de uma consultoria",
        "como faço para marcar horário?",
        "quero conversar com alguém",
        "preciso de suporte presencial",
        "gostaria de um encontro",
        "pode me ajudar com agendamento",
    ])
    def test_detecta_intencao_positiva(self, prompt):
        assert AgendaAnalista.detectar_intencao(prompt) is True

    @pytest.mark.parametrize("prompt", [
        "como analisar meu relatório?",
        "qual é o preço do plano?",
        "me explique os dados do excel",
        "o que é machine learning?",
        "",
    ])
    def test_nao_detecta_falso_positivo(self, prompt):
        assert AgendaAnalista.detectar_intencao(prompt) is False

    def test_case_insensitive(self):
        assert AgendaAnalista.detectar_intencao("QUERO AGENDAR UMA REUNIÃO") is True

    def test_frase_com_acento(self):
        assert AgendaAnalista.detectar_intencao("reunião com o consultor") is True


class TestValidarCampos:
    """Testa validações do formulário de agendamento."""

    def test_todos_campos_validos(self, agenda):
        erros = agenda._validar_campos(
            nome="William Santos",
            whatsapp="11999999999",
            email="william@teste.com",
        )
        assert erros == []

    def test_nome_vazio_gera_erro(self, agenda):
        erros = agenda._validar_campos(
            nome="",
            whatsapp="11999999999",
            email="william@teste.com",
        )
        assert any("nome" in e.lower() for e in erros)

    def test_whatsapp_vazio_gera_erro(self, agenda):
        erros = agenda._validar_campos(
            nome="William",
            whatsapp="",
            email="william@teste.com",
        )
        assert any("whatsapp" in e.lower() or "telefone" in e.lower() for e in erros)

    def test_email_invalido_gera_erro(self, agenda):
        erros = agenda._validar_campos(
            nome="William",
            whatsapp="11999999999",
            email="email-invalido",
        )
        assert any("email" in e.lower() for e in erros)

    def test_multiplos_campos_invalidos(self, agenda):
        erros = agenda._validar_campos(nome="", whatsapp="", email="")
        assert len(erros) >= 2
