from sqlalchemy import String, BigInteger, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from bd_oraculo_analista.models.model_base import ModelBase

class RespostaEnquete(ModelBase):
    __tablename__ = "resposta_enquete"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resposta: Mapped[str] = mapped_column(String(255), nullable=False)
    explicacao: Mapped[str] = mapped_column(Text, nullable=True)
    enquete_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("enquete.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # opcional: ForeignKey para UserAnalise
