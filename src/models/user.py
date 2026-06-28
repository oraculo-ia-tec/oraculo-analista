# ============================================================
# src/models/user.py
# Modelos ORM do Oráculo Analista
# ============================================================
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String

from .base import Base


class Cargo(Base):
    __tablename__ = "cargo"
    id   = Column(BigInteger, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)


class UserAdmin(Base):
    __tablename__ = "user_admin"
    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    name         = Column(String(100), nullable=False)
    cpf_cnpj     = Column(String(20))
    email        = Column(String(254), unique=True, nullable=False)
    whatsapp     = Column(String(15))
    endereco     = Column(String(255))
    cep          = Column(String(10))
    bairro       = Column(String(100))
    cidade       = Column(String(100))
    username     = Column(String(50))
    password     = Column(String(128))
    image        = Column(String(100))
    created_at   = Column(String(50))
    created_time = Column(String(50))
    deleted_at   = Column(String(50))
    deleted_time = Column(String(50))
    cargo_id     = Column(BigInteger, ForeignKey("cargo.id"))
    decisao      = Column(Boolean)
    culto_id     = Column(BigInteger)
    estado_civil = Column(String(20))
    filhos       = Column(Integer)


class UserAnalise(Base):
    __tablename__      = "user_analise"
    id                 = Column(Integer, primary_key=True)
    name               = Column(String(255), nullable=False)
    whatsapp           = Column(String(20), nullable=False)
    email              = Column(String(255), unique=True, nullable=False)
    password           = Column(String(255), nullable=False)
    profile_image_path = Column(String(500), nullable=True)
    verification_code  = Column(String(6), nullable=True)
    is_verified        = Column(Boolean, default=False)
    cargo_id           = Column(BigInteger, ForeignKey("cargo.id"), nullable=False)


class Enquete(Base):
    __tablename__ = "enquete"
    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    titulo        = Column(String(200))
    descricao     = Column(String)
    data_inicio   = Column(String)
    data_fim      = Column(String)
    ativo         = Column(Boolean)
    opcao1        = Column(String(200))
    opcao2        = Column(String(200))
    opcao3        = Column(String(200))
    opcao4        = Column(String(200))
    created_dt    = Column(String)
    updated_dt    = Column(String)
    cargo_id      = Column(BigInteger, ForeignKey("cargo.id"))


class RespostaEnquete(Base):
    __tablename__ = "resposta_enquete"
    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    resposta      = Column(String(255))
    explicacao    = Column(String)
    enquete_id    = Column(BigInteger, ForeignKey("enquete.id"))
    usuario_id    = Column(BigInteger, ForeignKey("user_analise.id"))


class DirecionadoEnquete(Base):
    __tablename__ = "direcionado_enquete"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    enquete_id    = Column(BigInteger, ForeignKey("enquete.id"))
    cargo_id      = Column(BigInteger, ForeignKey("cargo.id"))
