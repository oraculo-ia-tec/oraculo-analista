"""Página Dashboard — métricas e gráficos com Seaborn."""

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime


def render_dashboard(Session, UserAnalise, Cargo):
    st.header("📊 Dashboard")

    session = Session()
    try:
        usuarios = session.query(UserAnalise).all()
        cargos = {c.id: c.nome for c in session.query(Cargo).all()}
    finally:
        session.close()

    total_cadastrados = len(usuarios)
    verificados = sum(1 for u in usuarios if u.is_verified)
    nao_verificados = total_cadastrados - verificados

    # --- Métricas ---
    with st.container(border=True):
        st.subheader("Resumo Geral")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cadastrados", total_cadastrados)
        col2.metric("Verificados", verificados)
        col3.metric("Pendentes", nao_verificados)

    st.markdown("---")

    # --- Distribuição por cargo ---
    with st.container(border=True):
        st.subheader("Distribuição por Cargo")
        df = pd.DataFrame([
            {"Nome": u.name, "Email": u.email, "Cargo": cargos.get(u.cargo_id, "—"), "Verificado": u.is_verified}
            for u in usuarios
        ])

        if not df.empty:
            col_chart, col_table = st.columns([1, 1])
            with col_chart:
                fig, ax = plt.subplots(figsize=(5, 3))
                sns.countplot(data=df, x="Cargo", palette="viridis", ax=ax)
                ax.set_title("Usuários por Cargo")
                ax.set_ylabel("Quantidade")
                ax.set_xlabel("")
                plt.tight_layout()
                st.pyplot(fig)

            with col_table:
                st.dataframe(
                    df[["Nome", "Email", "Cargo", "Verificado"]],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("Nenhum usuário cadastrado.")

    st.markdown("---")

    # --- Status de verificação ---
    with st.container(border=True):
        st.subheader("Status de Verificação")
        if not df.empty:
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            verif_counts = df["Verificado"].value_counts().rename({True: "Verificado", False: "Pendente"})
            sns.barplot(x=verif_counts.index, y=verif_counts.values, palette="coolwarm", ax=ax2)
            ax2.set_title("Verificados vs Pendentes")
            ax2.set_ylabel("Quantidade")
            plt.tight_layout()
            st.pyplot(fig2)

    # --- Registro de acesso (simulado) ---
    with st.container(border=True):
        st.subheader("Último Acesso")
        st.caption("Horário atual do sistema")
        st.metric("Data/Hora", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
