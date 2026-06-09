"""
conftest.py — Configurações globais de teste (pytest)

Define:
  - Fixtures compartilhadas entre todos os módulos de teste
  - Configuração de variáveis de ambiente para testes
  - Limpeza de arquivos temporários
"""
import os
import pytest

# Garante que testes nunca chamem a API real do Groq
os.environ.setdefault("GROQ_API_KEY", "test_key_fake")
os.environ.setdefault("ORACULO_TEST_MODE", "true")


@pytest.fixture(autouse=True)
def reset_env():
    """Garante ambiente limpo entre testes."""
    yield
    # Cleanup após cada teste
    for key in ["ORACULO_CURRENT_USER", "ORACULO_CURRENT_SESSION"]:
        os.environ.pop(key, None)
