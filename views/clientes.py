"""Página Clientes — CRUD com tabs."""

import streamlit as st
import pandas as pd
import bcrypt


def render_clientes(Session, UserAnalise, Cargo):
    st.header("👥 Clientes")

    # Uma única consulta para cargo + lista de clientes
    session = Session()
    try:
        cargo_cliente = session.query(Cargo).filter_by(nome="Cliente").first()
        cargo_id_cliente = cargo_cliente.id if cargo_cliente else None
        clientes_raw = session.query(UserAnalise).filter_by(cargo_id=cargo_id_cliente).all() if cargo_id_cliente else []
        # Extrair dados antes de fechar a sessão
        clientes_data = [
            {"id": c.id, "name": c.name, "email": c.email, "whatsapp": c.whatsapp, "is_verified": c.is_verified}
            for c in clientes_raw
        ]
    finally:
        session.close()

    tab_listar, tab_criar, tab_editar, tab_deletar = st.tabs(
        ["📋 Listar", "➕ Criar", "✏️ Editar", "🗑️ Deletar"]
    )

    # --- LISTAR ---
    with tab_listar:
        if clientes_data:
            df = pd.DataFrame([
                {"ID": c["id"], "Nome": c["name"], "Email": c["email"], "WhatsApp": c["whatsapp"], "Verificado": c["is_verified"]}
                for c in clientes_data
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total de Clientes", len(clientes_data))
        else:
            st.info("Nenhum cliente encontrado.")

    # --- CRIAR ---
    with tab_criar:
        with st.container(border=True):
            st.subheader("Novo Cliente")
            nome = st.text_input("Nome", key="cli_nome")
            email = st.text_input("Email", key="cli_email")
            whatsapp = st.text_input("WhatsApp", key="cli_whatsapp")
            senha = st.text_input("Senha", type="password", key="cli_senha")

        # Upload de imagem fora do container/form para evitar erro
        imagem = st.file_uploader("Imagem de Perfil", type=["png", "jpg", "jpeg"], key="cli_img")
        if imagem:
            st.image(imagem, caption="Pré-visualização", width=150)

        if st.button("Cadastrar Cliente", key="btn_criar_cli"):
            if not all([nome, email, whatsapp, senha]):
                st.error("Preencha todos os campos.")
            elif not cargo_id_cliente:
                st.error("Cargo 'Cliente' não encontrado no banco.")
            else:
                session = Session()
                try:
                    existente = session.query(UserAnalise).filter_by(email=email).first()
                    if existente:
                        st.error("Email já cadastrado.")
                    else:
                        senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
                        image_path = None
                        if imagem and email:
                            import os
                            os.makedirs("./user_profiles/", exist_ok=True)
                            image_path = f"./user_profiles/{email}.png"
                            with open(image_path, "wb") as f:
                                f.write(imagem.getbuffer())
                        novo = UserAnalise(
                            name=nome, email=email, whatsapp=whatsapp,
                            password=senha_hash, is_verified=True,
                            cargo_id=cargo_id_cliente,
                            profile_image_path=image_path,
                        )
                        session.add(novo)
                        session.commit()
                        st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro: {e}")
                finally:
                    session.close()

    # --- EDITAR ---
    with tab_editar:
        with st.container(border=True):
            st.subheader("Editar Cliente")
            opcoes = {f"{c['name']} ({c['email']})": c["id"] for c in clientes_data}

            if opcoes:
                selecionado = st.selectbox("Selecione o cliente:", list(opcoes.keys()), key="sel_edit_cli")
                user_id = opcoes[selecionado]

                session = Session()
                try:
                    user = session.query(UserAnalise).get(user_id)
                    novo_nome = st.text_input("Nome", value=user.name, key="edit_cli_nome")
                    novo_whatsapp = st.text_input("WhatsApp", value=user.whatsapp, key="edit_cli_whatsapp")
                    novo_email = st.text_input("Email", value=user.email, key="edit_cli_email")

                    if st.button("Salvar Alterações", key="btn_edit_cli"):
                        user.name = novo_nome
                        user.whatsapp = novo_whatsapp
                        user.email = novo_email
                        session.commit()
                        st.success("Cliente atualizado com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro: {e}")
                finally:
                    session.close()
            else:
                st.info("Nenhum cliente para editar.")

    # --- DELETAR ---
    with tab_deletar:
        with st.container(border=True):
            st.subheader("Remover Cliente")
            opcoes_del = {f"{c['name']} ({c['email']})": c["id"] for c in clientes_data}

            if opcoes_del:
                selecionado_del = st.selectbox("Selecione o cliente:", list(opcoes_del.keys()), key="sel_del_cli")
                user_id_del = opcoes_del[selecionado_del]

                @st.dialog("Confirmar Exclusão")
                def confirmar_exclusao():
                    st.warning(f"Tem certeza que deseja remover **{selecionado_del}**?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Sim, remover", key="confirm_del_cli", type="primary"):
                            session = Session()
                            try:
                                user = session.query(UserAnalise).get(user_id_del)
                                if user:
                                    session.delete(user)
                                    session.commit()
                                    st.success("Cliente removido!")
                                    st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Erro: {e}")
                            finally:
                                session.close()
                    with col2:
                        if st.button("Cancelar", key="cancel_del_cli"):
                            st.rerun()

                if st.button("🗑️ Remover Cliente", key="btn_del_cli", type="primary"):
                    confirmar_exclusao()
            else:
                st.info("Nenhum cliente para remover.")
