# ============================================================
# src/models/migrate.py
# Migration automática — adiciona colunas novas sem apagar dados
# Compatível com SQLAlchemy 2.x
# ============================================================
from __future__ import annotations
import logging
from sqlalchemy import text
from .base import engine

logger = logging.getLogger("migration")

_COLUNAS_USER_ANALISE = [
    ("plano",                "VARCHAR(20)  DEFAULT 'free'"),
    ("pagamento_confirmado", "BOOLEAN      DEFAULT 0"),
    ("acesso_autorizado",    "BOOLEAN      DEFAULT 0"),
    ("upgrade_solicitado",   "VARCHAR(20)"),
    ("data_vencimento",      "DATE"),
    # imagem persistida como Base64 — sobrevive a deploys
    ("profile_image_b64",    "TEXT"),
]


def _colunas_existentes(conn, tabela: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({tabela})")).fetchall()
    return {row[1] for row in rows}


def rodar_migrations() -> None:
    with engine.connect() as conn:
        existentes = _colunas_existentes(conn, "user_analise")
        for col_nome, col_def in _COLUNAS_USER_ANALISE:
            if col_nome not in existentes:
                try:
                    conn.execute(text(f"ALTER TABLE user_analise ADD COLUMN {col_nome} {col_def}"))
                    conn.commit()
                    logger.info(f"Migration OK: '{col_nome}' adicionada.")
                except Exception as e:
                    logger.warning(f"Migration skip '{col_nome}': {e}")
            else:
                logger.debug(f"Migration: '{col_nome}' já existe.")
