from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.models.model_base import ModelBase


class Pagamento(ModelBase):
    """
    Tabela de pagamentos realizados por usuários.

    Cada pagamento pertence a um único usuário e registra
    data, valor, método e status da transação.
    """

    __tablename__ = "pagamentos"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    usuario_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )
    data_pagamento = sa.Column(
        sa.DateTime, nullable=False, default=datetime.utcnow)
    valor = sa.Column(sa.Numeric(10, 2), nullable=False)
    metodo_pagamento = sa.Column(sa.String(50), nullable=False)
    status_pagamento = sa.Column(
        sa.String(30), nullable=False, default="pendente")
    created_at = sa.Column(sa.DateTime, nullable=False,
                           default=datetime.utcnow)

    usuario = relationship(
        "Usuario",
        back_populates="pagamentos"
    )
