from sqlalchemy import String, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from bd_oraculo_analista.models.model_base import ModelBase

class UserAnalise(ModelBase):
    __tablename__ = "user_analise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    profile_image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    verification_code: Mapped[str] = mapped_column(String(6), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cargo.id"), nullable=False)  # ← ESTE
