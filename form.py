import streamlit as st

class FormAgenda:
    def __init__(self):
        self.nome = ""
        self.empresa = ""
        self.whatsapp = ""
        self.email = ""
        self.data = None
        self.hora = None

    def renderizar(self):
        with st.form("form_agendamento", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                self.nome = st.text_input("Nome completo", key="nome_agendamento")
                self.whatsapp = st.text_input("WhatsApp", key="whatsapp_agendamento")
                self.email = st.text_input("E-mail", key="email_agendamento")

            with col2:
                self.empresa = st.text_input("Empresa (opcional)", key="empresa_agendamento")
                self.data = st.date_input("Data", key="data_agendamento")
                self.hora = st.time_input("Horário", key="hora_agendamento")

            agendar = st.form_submit_button("Agendar")

        return agendar, {
            "nome": self.nome,
            "empresa": self.empresa,
            "whatsapp": self.whatsapp,
            "email": self.email,
            "data": str(self.data),
            "hora": str(self.hora)
        }
