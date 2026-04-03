"""Página Parceiros — CRUD com tabs."""

import streamlit as st
import pandas as pd
import bcrypt


def render_parceiros(Session, UserAnalise, Cargo):
    st.header("🤝 Parceiros")

    # Uma única consulta para cargo + lista de parceiros
    session = Session()
    try:
        cargo_parceiro = session.query(Cargo).filter_by(nome="Parceiro").first()
        cargo_id_parceiro = cargo_parceiro.id if cargo_parceiro else None
        parceiros_raw = session.query(UserAnalise).filter_by(cargo_id=cargo_id_parceiro).all() if cargo_id_parceiro else []
        parceiros_data = [
            {"id": p.id, "name": p.name, "email": p.email, "whatsapp": p.whatsapp, "is_verified": p.is_verified}
            for p in parceiros_raw
        ]
    finally:
        session.close()

    tab_listar, tab_criar, tab_editar, tab_deletar = st.tabs(
        ["📋 Listar", "➕ Criar", "✏️ Editar", "🗑️ Deletar"]
    )

    # --- LISTAR ---
    with tab_listar:
        if parceiros_data:
            df = pd.DataFrame([
                {"ID": p["id"], "Nome": p["name"], "Email": p["email"], "WhatsApp": p["whatsapp"], "Verificado": p["is_verified"]}
                for p in parceiros_data
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total de Parceiros", len(parceiros_data))
        else:
            st.info("Nenhum parceiro encontrado.")

    # --- CRIAR ---
    with tab_criar:
        with st.container(border=True):
            st.subheader("Novo Parceiro")
            nome = st.text_input("Nome", key="par_nome")
            email = st.text_input("Email", key="par_email")
            whatsapp = st.text_input("WhatsApp", key="par_whatsapp")
            senha = st.text_input("Senha", type="password", key="par_senha")

            if st.button("Cadastrar Parceiro", key="btn_criar_par"):
                if not all([nome, email, whatsapp, senha]):
                    st.error("Preencha todos os campos.")
                elif not cargo_id_parceiro:
                    st.error("Cargo 'Parceiro' não encontrado no banco. Cadastre o cargo primeiro.")
                else:
                    session = Session()
                    try:
                        existente = session.query(UserAnalise).filter_by(email=email).first()
                        if existente:
                            st.error("Email já cadastrado.")
                        else:
                            senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
                            novo = UserAnalise(
                                name=nome, email=email, whatsapp=whatsapp,
                                password=senha_hash, is_verified=True,
                                cargo_id=cargo_id_parceiro,
                            )
                            session.add(novo)
                            session.commit()
                            st.success(f"Parceiro '{nome}' cadastrado com sucesso!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro: {e}")
                    finally:
                        session.close()

    # --- EDITAR ---
    with tab_editar:
        with st.container(border=True):
            st.subheader("Editar Parceiro")
            opcoes = {f"{p['name']} ({p['email']})": p["id"] for p in parceiros_data}

            if opcoes:
                selecionado = st.selectbox("Selecione o parceiro:", list(opcoes.keys()), key="sel_edit_par")
                user_id = opcoes[selecionado]

                session = Session()
                try:
                    user = session.query(UserAnalise).get(user_id)
                    novo_nome = st.text_input("Nome", value=user.name, key="edit_par_nome")
                    novo_whatsapp = st.text_input("WhatsApp", value=user.whatsapp, key="edit_par_whatsapp")
                    novo_email = st.text_input("Email", value=user.email, key="edit_par_email")

                    if st.button("Salvar Alterações", key="btn_edit_par"):
                        user.name = novo_nome
                        user.whatsapp = novo_whatsapp
                        user.email = novo_email
                        session.commit()
                        st.success("Parceiro atualizado com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro: {e}")
                finally:
                    session.close()
            else:
                st.info("Nenhum parceiro para editar.")

    # --- DELETAR ---
    with tab_deletar:
        with st.container(border=True):
            st.subheader("Remover Parceiro")
            opcoes_del = {f"{p['name']} ({p['email']})": p["id"] for p in parceiros_data}

            if opcoes_del:
                selecionado_del = st.selectbox("Selecione o parceiro:", list(opcoes_del.keys()), key="sel_del_par")
                user_id_del = opcoes_del[selecionado_del]

                @st.dialog("Confirmar Exclusão")
                def confirmar_exclusao_par():
                    st.warning(f"Tem certeza que deseja remover **{selecionado_del}**?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Sim, remover", key="confirm_del_par", type="primary"):
                            session = Session()
                            try:
                                user = session.query(UserAnalise).get(user_id_del)
                                if user:
                                    session.delete(user)
                                    session.commit()
                                    st.success("Parceiro removido!")
                                    st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Erro: {e}")
                            finally:
                                session.close()
                    with col2:
                        if st.button("Cancelar", key="cancel_del_par"):
                            st.rerun()

                if st.button("🗑️ Remover Parceiro", key="btn_del_par", type="primary"):
                    confirmar_exclusao_par()
            else:
                st.info("Nenhum parceiro para remover.")
