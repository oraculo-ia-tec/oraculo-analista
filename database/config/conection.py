import sqlalchemy as sa
from typing import Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from database.models.model_base import ModelBase


__engine: Optional[Engine] = None
SessionLocal = None


def get_engine() -> Engine:
    """
    Configura e retorna a engine de conexão com o banco SQLite.

    Returns:
        Engine: instância única da engine do SQLAlchemy.
    """
    global __engine

    if __engine is not None:
        return __engine

    conn_str = "sqlite:///oraculo_analista.db"
    __engine = sa.create_engine(
        conn_str,
        echo=False,
        connect_args={"check_same_thread": False}
    )

    return __engine


def create_session() -> Session:
    """
    Cria e retorna uma nova sessão do banco de dados.

    Returns:
        Session: sessão ativa do SQLAlchemy.
    """
    global SessionLocal

    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session
        )

    return SessionLocal()


def create_tables() -> None:
    """
    Cria todas as tabelas registradas no metadata do projeto.
    """
    engine = get_engine()

    try:
        import database.models.__all_models

        print("🔄 Criando as tabelas no banco de dados...")
        ModelBase.metadata.create_all(engine)
        print("✅ Tabelas criadas com sucesso!")
        print("📋 Tabelas registradas:")

        for table_name in ModelBase.metadata.tables.keys():
            print(f" - {table_name}")

    except Exception as e:
        print("❌ Erro ao criar as tabelas!")
        print(f"Detalhes: {e}")
        raise
