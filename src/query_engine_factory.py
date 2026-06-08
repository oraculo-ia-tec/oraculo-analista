"""
Fábrica de QueryEngine.
Cria uma instância completa do QueryEngine com todos os
dependências já instanciadas e prontas para uso.

Uso no app.py:
  from src.query_engine_factory import create_engine
  engine = create_engine(user_id, user_name, user_email, user_plan)
  response = engine.run(user_input)
"""
from src.memory.memory_manager import MemoryManager
from src.query_engine import QueryEngine
from src.tools.registry_loader import load_all_tools
from src.types.base import SessionState, UserProfile
from src.utils.helpers import generate_id


# Garante que todas as tools estão registradas ao importar a fábrica
load_all_tools()


def create_engine(
    user_id: str,
    user_name: str = "",
    user_email: str = "",
    user_plan: str = "free",
) -> QueryEngine:
    """
    Cria e retorna um QueryEngine completamente inicializado.

    Args:
        user_id:    ID único do usuário (do banco de dados)
        user_name:  Nome do usuário para personalização
        user_email: E-mail do usuário
        user_plan:  Plano do usuário (free/pro/enterprise)

    Returns:
        QueryEngine pronto para receber chamadas .run()
    """
    # 1. Perfil do usuário
    user = UserProfile(
        user_id=user_id,
        name=user_name,
        email=user_email,
        plan=user_plan,
    )

    # 2. Estado da sessão
    session = SessionState(
        session_id=generate_id("session"),
        user=user,
    )

    # 3. Memória persistente do usuário
    memory = MemoryManager(
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
    )

    # 4. Instancia e retorna o engine
    return QueryEngine(session=session, memory=memory)
