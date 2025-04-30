from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from model_base import ModelBase  # Importando ModelBase


# Modelo de Usuário no Banco de Dados
class UserAnalise(Base):
    __tablename__ = "user_analise"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    profile_image_path = Column(String(500), nullable=True)
    verification_code = Column(String(6), nullable=True)
    is_verified = Column(String(10), default="false")
    password = Column(String(255), nullable=True)