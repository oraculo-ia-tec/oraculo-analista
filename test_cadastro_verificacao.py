"""Script de cadastro de teste para verificar autenticação, verificação e acesso."""
import os
import shutil
import random
import string

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import UserAnalise, Cargo, Base
from notification import Notificador

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///oraculo_analista.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Dados do teste
NAME = "Laughing Man"
WHATSAPP = "11988887777"
EMAIL = "rededescpro@gmail.com"
PASSWORD = "teste123"
IMAGE_SRC = "src/img/laughter-man.jpg"
CARGO_ID = 3  # Cliente


def main():
    session = Session()
    try:
        # Remove cadastro anterior se existir
        existente = session.query(UserAnalise).filter_by(email=EMAIL).first()
        if existente:
            print(f"Usuário {EMAIL} já existe. Removendo para novo teste...")
            session.delete(existente)
            session.commit()

        # Copiar imagem de perfil
        image_path = None
        if os.path.exists(IMAGE_SRC):
            os.makedirs("./user_profiles/", exist_ok=True)
            dest = f"./user_profiles/{EMAIL}.jpg"
            shutil.copy2(IMAGE_SRC, dest)
            image_path = dest
            print(f"Imagem copiada: {IMAGE_SRC} -> {dest}")
        else:
            print(f"AVISO: Imagem não encontrada em {IMAGE_SRC}")

        # Gerar código e hash da senha
        codigo = "".join(random.choices(string.digits, k=6))
        senha_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

        # Buscar nome do cargo
        cargo = session.query(Cargo).filter_by(id=CARGO_ID).first()
        cargo_nome = cargo.nome if cargo else "Cliente"

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

        print(f"\n{'='*50}")
        print(f"  CADASTRO DE TESTE REALIZADO")
        print(f"{'='*50}")
        print(f"  Nome:    {NAME}")
        print(f"  Email:   {EMAIL}")
        print(f"  Senha:   {PASSWORD}")
        print(f"  Cargo:   {cargo_nome}")
        print(f"  Código:  {codigo}")
        print(f"  Imagem:  {image_path}")
        print(f"{'='*50}")

        # Enviar e-mails
        print("\nEnviando e-mail de boas-vindas...")
        notificador = Notificador()
        notificador.enviar_boas_vindas(NAME, EMAIL, WHATSAPP, cargo=cargo_nome)
        print("✅ E-mail de boas-vindas enviado!")

        print("Enviando e-mail de verificação...")
        notificador.enviar_verificacao(NAME, EMAIL, codigo)
        print("✅ E-mail de verificação enviado!")

        print(f"\n>> Use o código {codigo} para verificar a conta no sistema.")
        print(f">> Login: {EMAIL} / {PASSWORD}")

    except Exception as e:
        session.rollback()
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
