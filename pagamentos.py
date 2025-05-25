import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Date
from decouple import config
import datetime
from notification import Notificador, WhatsAppSimulado


st.set_page_config(page_title="Pagamentos - Oráculo Analista", layout="wide")

st.title("💳 Painel de Pagamentos")

STATUS_OPTIONS = ["PENDENTE", "RECEBIDO", "CONFIRMADO", "VENCIDO"]
STATUS_TRANSLATE = {
    "PENDING": "PENDENTE",
    "RECEIVED": "RECEBIDO",
    "CONFIRMED": "CONFIRMADO",
    "OVERDUE": "VENCIDO"
}

# Configurações do notificador
notificador = Notificador(
    smtp_server="smtp.seuservidor.com",
    smtp_port=587,
    login="seu@email.com",
    senha="sua_senha"
)

reverse_translate = {v: k for k, v in STATUS_TRANSLATE.items()}
status = st.selectbox("Filtrar pagamentos por status:", options=STATUS_OPTIONS, index=0)

with st.spinner("Carregando dados..."):
    try:
        api_status = reverse_translate[status]
        response = requests.get(f"http://localhost:8000/listar-pagamentos?status={api_status}")
        pagamentos = response.json().get("data", [])

        if not pagamentos:
            st.warning("Nenhum pagamento encontrado com esse status.")
        else:
            df = pd.DataFrame(pagamentos)
            colunas_desejadas = ["customer", "value", "billingType", "status", "dueDate", "id"]
            df = df[colunas_desejadas]
            df = df.rename(columns={
                "customer": "Cliente",
                "value": "Valor",
                "billingType": "Tipo",
                "status": "Status",
                "dueDate": "Vencimento",
                "id": "ID do Pagamento"
            })
            df["Status"] = df["Status"].map(STATUS_TRANSLATE)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao buscar pagamentos: {e}")

st.markdown("---")
st.subheader("🔍 Verificar pagamento manualmente")
payment_id = st.text_input("Informe o ID do pagamento para verificar:")

# Configuração do banco para atualização
DATABASE_URL = config("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class UserAnalise(Base):
    __tablename__ = "user_analise"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image_path = Column(String(500), nullable=True)
    verification_code = Column(String(6), nullable=True)
    is_verified = Column(Boolean, default=False)
    plano = Column(String(20), default="free")
    pagamento_verificado = Column(Boolean, default=False)
    upgrade_solicitado = Column(String(20), nullable=True)
    pagamento_confirmado = Column(Boolean, default=False)
    acesso_autorizado = Column(Boolean, default=False)
    data_vencimento = Column(Date, nullable=True)

if st.button("Verificar Pagamento"):
    try:
        resposta = requests.post("http://localhost:8000/verificar-pagamento", json={"payment_id": payment_id})
        dados = resposta.json()
        status_pagamento = dados.get("status", "indefinido")
        cliente_id = dados.get("customer", None)

        status_br = STATUS_TRANSLATE.get(status_pagamento, status_pagamento)
        st.success(f"Status do pagamento {payment_id}: {status_br}")

        if status_pagamento == "RECEIVED" and cliente_id:
            session = Session()
            usuario = session.query(UserAnalise).filter_by(email=cliente_id).first()
            if usuario:
                usuario.pagamento_confirmado = True
                usuario.acesso_autorizado = True
                usuario.plano = usuario.upgrade_solicitado
                dias = 30 if usuario.plano == "mensal" else 90 if usuario.plano == "trimestral" else 365
                usuario.data_vencimento = datetime.date.today() + datetime.timedelta(days=dias)
                session.commit()
                st.success("Status do usuário atualizado no banco de dados.")
            else:
                st.warning("Usuário com e-mail correspondente ao cliente não encontrado.")
            session.close()

    except Exception as e:
        st.error(f"Erro ao verificar pagamento: {e}")
