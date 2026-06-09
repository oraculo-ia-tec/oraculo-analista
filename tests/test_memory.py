"""
Testes automatizados — Sistema de Memória

Cobre:
  - MemoryManager: leitura, escrita e atualização
  - SessionStore: persistência de sessões
  - Limites de contexto e truncamento
"""
import os
import json
import tempfile
import pytest

from src.memory.memory_manager import MemoryManager
from src.memory.session_store import SessionStore
from src.types.base import SessionState
from src.utils.helpers import generate_id


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def memory(tmp_dir):
    return MemoryManager(user_id="test_user", base_dir=tmp_dir)


@pytest.fixture
def session():
    return SessionState(
        session_id=generate_id("test"),
        user_id="test_user",
        messages=[],
        total_tokens=0,
        tool_calls_count=0,
        active_document=None,
    )


# ─── MemoryManager ────────────────────────────────────────────────────────────

class TestMemoryManager:
    def test_cria_arquivo_memoria(self, memory, tmp_dir):
        memory.save("nome_usuario", "João")
        assert os.path.exists(os.path.join(tmp_dir, "test_user", "MEMORY.md"))

    def test_salva_e_recupera(self, memory):
        memory.save("preferencia", "gráficos de barra")
        valor = memory.get("preferencia")
        assert valor == "gráficos de barra"

    def test_atualiza_valor(self, memory):
        memory.save("empresa", "Acme")
        memory.save("empresa", "TechCorp")
        assert memory.get("empresa") == "TechCorp"

    def test_chave_inexistente_retorna_none(self, memory):
        assert memory.get("chave_nao_existe") is None

    def test_multiplos_valores(self, memory):
        memory.save("a", "1")
        memory.save("b", "2")
        memory.save("c", "3")
        assert memory.get("a") == "1"
        assert memory.get("b") == "2"
        assert memory.get("c") == "3"

    def test_contexto_formatado(self, memory):
        memory.save("nome", "Maria")
        ctx = memory.get_context()
        assert "Maria" in ctx
        assert "nome" in ctx.lower()

    def test_context_vazio(self, memory):
        ctx = memory.get_context()
        assert isinstance(ctx, str)


# ─── SessionStore ─────────────────────────────────────────────────────────────

class TestSessionStore:
    def test_salva_e_carrega_sessao(self, session, tmp_dir):
        store = SessionStore(user_id="test_user", base_dir=tmp_dir)
        store.save(session)

        loaded = store.load(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.user_id == session.user_id

    def test_sessao_inexistente_retorna_none(self, tmp_dir):
        store = SessionStore(user_id="test_user", base_dir=tmp_dir)
        assert store.load("id_que_nao_existe") is None

    def test_lista_sessoes(self, session, tmp_dir):
        store = SessionStore(user_id="test_user", base_dir=tmp_dir)
        store.save(session)
        sessions = store.list_sessions()
        assert session.session_id in [s["session_id"] for s in sessions]

    def test_multiplas_sessoes(self, tmp_dir):
        store = SessionStore(user_id="test_user", base_dir=tmp_dir)
        for i in range(3):
            s = SessionState(
                session_id=f"session_{i}",
                user_id="test_user",
                messages=[],
                total_tokens=i * 100,
                tool_calls_count=i,
                active_document=None,
            )
            store.save(s)

        sessions = store.list_sessions()
        assert len(sessions) == 3
