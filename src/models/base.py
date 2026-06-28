# ============================================================
# src/models/base.py
# Engine, Session e Base — fonte única de conexão com o banco
# ============================================================
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _get_database_url() -> str:
    try:
        return st.secrets["default"]["DATABASE_URL"]
    except Exception:
        return "sqlite:///oraculo_analista.db"


DATABASE_URL = _get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
Session = sessionmaker(bind=engine)
Base    = declarative_base()
