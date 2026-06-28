# ============================================================
# src/payments/models.py
# Modelos ORM de pagamento — sem dependências de UI
# ============================================================
from __future__ import annotations

import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime,
    Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from ..models.base import Base


class UserAnalisePayment(Base):
    """
    Extensão de pagamento do UserAnalise.
    Adicionada via alter table — colunas são nullable para retrocompatibilidade.
    """
    __tablename__ = "user_analise"
    __table_args__ = {"extend_existing": True}

    id                   = Column(Integer, primary_key=True)
    plano                = Column(String(20),  default="free")
    pagamento_confirmado = Column(Boolean,     default=False)
    acesso_autorizado    = Column(Boolean,     default=False)
    upgrade_solicitado   = Column(String(20),  nullable=True)
    data_vencimento      = Column(Date,        nullable=True)


class Cobranca(Base):
    __tablename__ = "cobrancas"

    id            = Column(Integer,  primary_key=True, autoincrement=True)
    user_id       = Column(Integer,  ForeignKey("user_analise.id"), nullable=False)
    plano         = Column(String(20), nullable=False)
    valor         = Column(Float,    nullable=False)
    status        = Column(String(20), nullable=False, default="PENDING")  # PENDING | PAID | CANCELLED
    data_criacao  = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    due_date      = Column(Date,     nullable=False)
    descricao     = Column(Text,     nullable=True)
    payment_link  = Column(String,   nullable=True)
    asaas_id      = Column(String,   nullable=True)  # ID retornado pela API Asaas

    pagamentos = relationship("Pagamento", back_populates="cobranca", cascade="all, delete-orphan")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    cobranca_id = Column(Integer, ForeignKey("cobrancas.id"), nullable=False)
    valor_pago  = Column(Float,   nullable=False)
    status      = Column(String(20), nullable=False, default="PENDING")  # PENDING | PAID | REFUNDED
    data_pago   = Column(DateTime, nullable=True)
    payment_id  = Column(String,  nullable=True)   # ID da API Asaas
    descricao   = Column(Text,    nullable=True)

    cobranca = relationship("Cobranca", back_populates="pagamentos")
