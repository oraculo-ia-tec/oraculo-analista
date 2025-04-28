from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from model_base import ModelBase  # Importando ModelBase


# Modelo de Usuário no Banco de Dados
class UserAnalise(Base):
    __tablename__ = "user_analise"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    whatsapp = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    profile_image_path = Column(String, nullable=True)  # Caminho da imagem de perfil
    verification_code = Column(String, nullable=True)   # Código de verificação
    is_verified = Column(String, default="false")       # Status de verificação