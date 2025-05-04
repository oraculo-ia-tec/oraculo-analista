from sqlalchemy import String, BigInteger, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from bd_oraculo_analista.models.model_base import ModelBase

class Enquete(ModelBase):
    __tablename__ = "enquete"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    data_inicio: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    data_fim: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    opcao1: Mapped[str] = mapped_column(String(200), nullable=True)
    opcao2: Mapped[str] = mapped_column(String(200), nullable=True)
    opcao3: Mapped[str] = mapped_column(String(200), nullable=True)
    opcao4: Mapped[str] = mapped_column(String(200), nullable=True)
    created_dt: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_dt: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    cargo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cargo.id"), nullable=False)
