"""Script de teste para cadastro e envio de e-mail de verificação."""
from notification import Notificador
from app import UserAnalise, Base
import os
import random
import string
import shutil

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///oraculo_analista.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Importa o modelo e o notificador

# Dados do teste
NAME = "William Teste"
WHATSAPP = "11999999999"
EMAIL = "williamllider@gmail.com"
PASSWORD = "teste123"
IMAGE_SRC = "src/img/william.jpg"
CARGO_ID = 3  # Cliente


def main():
    session = Session()
    try:
        # Verifica se já existe
        existente = session.query(UserAnalise).filter_by(email=EMAIL).first()
        if existente:
            print(f"Usuário {EMAIL} já existe. Removendo para novo teste...")
            session.delete(existente)
            session.commit()

        # Salvar imagem de perfil
        image_path = None
        if os.path.exists(IMAGE_SRC):
            dest = f"./user_profiles/{EMAIL}.jpg"
            shutil.copy2(IMAGE_SRC, dest)
            image_path = dest
            print(f"Imagem copiada: {IMAGE_SRC} -> {dest}")
        else:
            print(f"AVISO: Imagem não encontrada em {IMAGE_SRC}")

        # Gerar código e hash da senha
        codigo = "".join(random.choices(string.digits, k=6))
        senha_hash = bcrypt.hashpw(
            PASSWORD.encode(), bcrypt.gensalt()).decode()

        # Criar usuário
        novo = UserAnalise(
            name=NAME,
            whatsapp=WHATSAPP,
            email=EMAIL,
            password=senha_hash,
            profile_image_path=image_path,
            verification_code=codigo,
            is_verified=False,
            cargo_id=CARGO_ID,
        )
        session.add(novo)
        session.commit()
        print(f"Usuário cadastrado: {EMAIL}")
        print(f"Código de verificação: {codigo}")

        # Enviar e-mail
        print("Enviando e-mail de verificação...")
        notificador = Notificador()
        assunto = "Código de Verificação - Oráculo Analista"
        mensagem = f"""
        <h3>Olá, {NAME}</h3>
        <p>Seu código de verificação para o Oráculo Analista é: <strong>{codigo}</strong></p>
        <p>Use este código para ativar sua conta.</p>
        """
        resposta = notificador.enviar_email(EMAIL, assunto, mensagem)
        print(f"E-mail enviado com sucesso! ID: {resposta.get('id')}")

    except Exception as e:
        session.rollback()
        print(f"ERRO: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
