import streamlit as st

with st.popover("Agendamento"):
    st.markdown("### 📅 Agende uma reunião com o Oráculo Analista")
    nome = st.text_input("Nome completo")
    empresa = st.text_input("Empresa (opcional)")
    whatsapp = st.text_input("WhatsApp")
    email = st.text_input("E-mail")
    data = st.date_input("Data")
    hora = st.time_input("Horário")

    if st.button("Cadastrar"):
        st.write("Nome:", nome)
        st.write("Empresa:", empresa)
        st.write("WhatsApp:", whatsapp)
        st.write("E-mail:", email)
        st.write("Data:", data)
        st.write("Horário:", hora)

import streamlit as st

# Popover para escolher o plano
with st.popover("ESCOLHA SEU PLANO"):
    st.markdown("### 💼 Planos Oráculo Analista")
    st.write("Escolha um dos planos abaixo para liberar recursos avançados.")

    # Criando duas colunas
    col1, col2 = st.columns(2)

    with col1:
        # Apresentar os planos
        plano = st.radio("Selecione um plano:",
                         ["Mensal - R$ 49,90", "Trimestral - R$ 119,90", "Anual - R$ 369,90"])

    with col2:
        # Breve descrição de cada plano
        if plano == "Mensal - R$ 49,90":
            st.write("Ideal para quem deseja experimentar nossos serviços por um curto período.")
        elif plano == "Trimestral - R$ 119,90":
            st.write("Economize em relação ao plano mensal e tenha mais tempo para aproveitar.")
        elif plano == "Anual - R$ 369,90":
            st.write("A melhor opção para quem deseja um compromisso a longo prazo com descontos significativos.")

    if st.button("Assinar agora"):
        if plano == "Mensal - R$ 49,90":
            st.write("Você será redirecionado para o link de simulação do plano mensal.")
            st.markdown("[Clique aqui para assinatura mensal](https://sandbox.asaas.com/c/qmo94xid8f1i6tnc)")
        elif plano == "Trimestral - R$ 119,90":
            st.write("Você será redirecionado para o link de simulação do plano trimestral.")
            st.markdown("[Clique aqui para assinatura trimestral](https://sandbox.asaas.com/c/jsmak76vdo5fke23)")
        elif plano == "Anual - R$ 369,90":
            st.write("Você será redirecionado para o link de simulação do plano anual.")
            st.markdown("[Clique aqui para assinatura anual](https://sandbox.asaas.com/c/adu6nd24lf8jauo3)")



