"""Página Financeiro / Pagamentos — com tabs."""

import streamlit as st
import pandas as pd
from datetime import datetime, date


def render_financeiro(Session, UserAnalise, Cargo):
    st.header("💰 Financeiro")

    tab_resumo, tab_cobr, tab_hist = st.tabs(
        ["📊 Resumo", "💳 Cobranças", "📋 Histórico"]
    )

    # --- RESUMO ---
    with tab_resumo:
        with st.container(border=True):
            st.subheader("Resumo Financeiro")

            session = Session()
            try:
                total_usuarios = session.query(UserAnalise).count()
                verificados = session.query(UserAnalise).filter_by(is_verified=True).count()
            finally:
                session.close()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Usuários", total_usuarios)
            col2.metric("Ativos (Verificados)", verificados)
            col3.metric("Data Atual", date.today().strftime("%d/%m/%Y"))

            st.markdown("---")
            st.caption("Integração com gateway de pagamento em desenvolvimento.")

    # --- COBRANÇAS ---
    with tab_cobr:
        with st.container(border=True):
            st.subheader("Gerar Cobrança")
            session = Session()
            try:
                usuarios = session.query(UserAnalise).filter_by(is_verified=True).all()
                opcoes = {f"{u.name} ({u.email})": u.id for u in usuarios}
            finally:
                session.close()

            if opcoes:
                selecionado = st.selectbox("Selecione o usuário:", list(opcoes.keys()), key="fin_user")
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, key="fin_valor")
                vencimento = st.date_input("Data de Vencimento", key="fin_venc")
                descricao = st.text_area("Descrição", key="fin_desc")

                if st.button("Gerar Cobrança", key="btn_gerar_cob"):
                    st.success(f"Cobrança de R$ {valor:.2f} gerada para {selecionado} com vencimento em {vencimento.strftime('%d/%m/%Y')}.")
                    st.caption("Integração com API de pagamento será implementada em breve.")
            else:
                st.info("Nenhum usuário verificado para gerar cobrança.")

    # --- HISTÓRICO ---
    with tab_hist:
        with st.container(border=True):
            st.subheader("Histórico de Pagamentos")
            st.info("Histórico será exibido quando a integração com gateway estiver ativa.")

            # Dados de exemplo para demonstração
            dados_demo = [
                {"Usuário": "Exemplo", "Valor": 99.90, "Status": "PAGO", "Data": "01/04/2026"},
                {"Usuário": "Exemplo 2", "Valor": 149.90, "Status": "PENDENTE", "Data": "02/04/2026"},
            ]
            df = pd.DataFrame(dados_demo)
            st.dataframe(df, width='stretch', hide_index=True)
