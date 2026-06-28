# ============================================================
# src/models/migrate.py
# Migration automática — adiciona colunas novas sem apagar dados
# Chamado uma vez ao iniciar o app (seguro rodar várias vezes)
# ============================================================
from __future__ import annotations

import logging

from .base import engine

logger = logging.getLogger("migration")

# Colunas a garantir em user_analise: (nome, definição SQL)
_COLUNAS_USER_ANALISE = [
    ("plano",                "VARCHAR(20)  DEFAULT 'free'"),
    ("pagamento_confirmado", "BOOLEAN      DEFAULT 0"),
    ("acesso_autorizado",    "BOOLEAN      DEFAULT 0"),
    ("upgrade_solicitado",   "VARCHAR(20)"),
    ("data_vencimento",      "DATE"),
]


def _colunas_existentes(conn, tabela: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    return {row[1] for row in rows}   # row[1] = nome da coluna


def rodar_migrations() -> None:
    """
    Adiciona colunas ausentes na tabela user_analise.
    Usa PRAGMA table_info para não duplicar colunas já existentes.
    """
    with engine.connect() as conn:
        existentes = _colunas_existentes(conn, "user_analise")

        for col_nome, col_def in _COLUNAS_USER_ANALISE:
            if col_nome not in existentes:
                sql = f"ALTER TABLE user_analise ADD COLUMN {col_nome} {col_def}"
                try:
                    conn.execute(__import__("sqlalchemy").text(sql))
                    conn.commit()
                    logger.info(f"Migration OK: coluna '{col_nome}' adicionada.")
                except Exception as e:
                    logger.warning(f"Migration skip '{col_nome}': {e}")
            else:
                logger.debug(f"Migration: coluna '{col_nome}' já existe.")
