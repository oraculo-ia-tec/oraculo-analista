from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from bd_oraculo_analista.models.model_base import ModelBase

class DirecionadoEnquete(ModelBase):
    __tablename__ = "direcionado_enquete"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enquete_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("enquete.id"), nullable=False)
    cargo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cargo.id"), nullable=False)
