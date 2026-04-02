from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.models.model_base import ModelBase


class Usuario(ModelBase):
    """
    Tabela de usuários do sistema.

    Armazena os dados principais de autenticação, contato e
    referência da imagem de perfil do usuário.
    """

    __tablename__ = "usuarios"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nome = sa.Column(sa.String(255), nullable=False)
    whatsapp = sa.Column(sa.String(20), nullable=False, unique=True)
    email = sa.Column(sa.String(255), nullable=False, unique=True, index=True)
    senha_hash = sa.Column(sa.String(255), nullable=False)
    imagem_perfil = sa.Column(sa.String(500), nullable=True)
    created_at = sa.Column(sa.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    pagamentos = relationship(
        "Pagamento",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
