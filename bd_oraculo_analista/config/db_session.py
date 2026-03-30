import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.future.engine import Engine
from bd_oraculo_analista.models.model_base import ModelBase


__engine: Optional[Engine] = None


def create_engine() -> Engine:
    """
    Função para configurar a conexão ao banco de dados SQLite.
    """
    global __engine

    if __engine:
        return __engine

    # String de conexão para SQLite
    conn_str = "sqlite:///oraculo_analista.db"
    __engine = sa.create_engine(url=conn_str, echo=False)

    return __engine


def create_session() -> Session:
    """
    Função para criar sessão de conexão ao banco de dados.
    """
    global __engine

    if not __engine:
        create_engine()

    __session = sessionmaker(__engine, expire_on_commit=False, class_=Session)

    session: Session = __session()

    return session


def create_tables() -> None:
    global __engine

    if not __engine:
        create_engine()

    try:
        # Garante que todas as classes sejam registradas
        import bd_oraculo_analista.models.__all_models

        print("🔄 Criando as tabelas no banco de dados...")
        ModelBase.metadata.create_all(__engine)
        print("✅ Tabelas criadas com sucesso!")
        print("📋 Tabelas registradas:")
        for table_name in ModelBase.metadata.tables.keys():
            print(f"  - {table_name}")

    except Exception as e:
        print("❌ Erro ao criar as tabelas!")
        print(f"Detalhes: {e}")
