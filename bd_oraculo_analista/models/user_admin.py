from sqlalchemy import String, Integer, BigInteger, Date, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from bd_oraculo_analista.models.model_base import ModelBase


class UserAdmin(ModelBase):
    __tablename__ = "user_admin"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    whatsapp: Mapped[str] = mapped_column(String(15), nullable=False)
    endereco: Mapped[str] = mapped_column(String(255), nullable=True)
    cep: Mapped[str] = mapped_column(String(10), nullable=True)
    bairro: Mapped[str] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str] = mapped_column(String(100), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    image: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Date] = mapped_column(Date, nullable=True)
    created_time: Mapped[Time] = mapped_column(Time, nullable=True)
    deleted_at: Mapped[Date] = mapped_column(Date, nullable=True)
    deleted_time: Mapped[Time] = mapped_column(Time, nullable=True)
    cargo_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    decisao: Mapped[bool] = mapped_column(Boolean, default=False)
    culto_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    estado_civil: Mapped[str] = mapped_column(String(20), nullable=True)
    filhos: Mapped[int] = mapped_column(Integer, nullable=True)
