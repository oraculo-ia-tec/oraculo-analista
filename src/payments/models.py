# ============================================================
# src/payments/models.py
# Modelos ORM de cobranças e pagamentos
# UserAnalise é importado de src.models.user — sem redeclaração
# ============================================================
from __future__ import annotations

import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime,
    Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from ..models.base import Base


class Cobranca(Base):
    __tablename__ = "cobrancas"

    id            = Column(Integer,    primary_key=True, autoincrement=True)
    user_id       = Column(Integer,    ForeignKey("user_analise.id"), nullable=False)
    plano         = Column(String(20), nullable=False)
    valor         = Column(Float,      nullable=False)
    status        = Column(String(20), nullable=False, default="PENDING")
    data_criacao  = Column(DateTime,   nullable=False, default=datetime.datetime.utcnow)
    due_date      = Column(Date,       nullable=False)
    descricao     = Column(Text,       nullable=True)
    payment_link  = Column(String,     nullable=True)
    asaas_id      = Column(String,     nullable=True)

    pagamentos = relationship("Pagamento", back_populates="cobranca", cascade="all, delete-orphan")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id          = Column(Integer,    primary_key=True, autoincrement=True)
    cobranca_id = Column(Integer,    ForeignKey("cobrancas.id"), nullable=False)
    valor_pago  = Column(Float,      nullable=False)
    status      = Column(String(20), nullable=False, default="PENDING")
    data_pago   = Column(DateTime,   nullable=True)
    payment_id  = Column(String,     nullable=True)
    descricao   = Column(Text,       nullable=True)

    cobranca = relationship("Cobranca", back_populates="pagamentos")
