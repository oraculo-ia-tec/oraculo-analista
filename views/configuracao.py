"""Página Configuração — ajustes do sistema com tabs."""

import streamlit as st
import bcrypt


def render_configuracao(Session, UserAnalise, Cargo):
    st.header("⚙️ Configuração")

    user = st.session_state.get("user")
    if not user:
        st.error("Usuário não autenticado.")
        return

    tab_perfil, tab_senha, tab_sistema, tab_cargos = st.tabs(
        ["👤 Perfil", "🔒 Alterar Senha", "🖥️ Sistema", "🏷️ Cargos"]
    )

    # --- PERFIL ---
    with tab_perfil:
        with st.container(border=True):
            st.subheader("Meus Dados")

            session = Session()
            try:
                u = session.query(UserAnalise).get(user.id)
                if not u:
                    st.error("Usuário não encontrado.")
                    return

                novo_nome = st.text_input("Nome", value=u.name, key="cfg_nome")
                novo_whatsapp = st.text_input("WhatsApp", value=u.whatsapp, key="cfg_whatsapp")
                st.text_input("Email", value=u.email, disabled=True, key="cfg_email")

                nova_imagem = st.file_uploader("Foto de Perfil", type=["png", "jpg", "jpeg"], key="cfg_img")
                if nova_imagem:
                    st.image(nova_imagem, caption="Pré-visualização", width=150)

                if st.button("Salvar Perfil", key="btn_save_perfil"):
                    u.name = novo_nome
                    u.whatsapp = novo_whatsapp
                    if nova_imagem:
                        import os
                        path = f"./user_profiles/{u.email}.png"
                        with open(path, "wb") as f:
                            f.write(nova_imagem.getbuffer())
                        u.profile_image_path = path
                    session.commit()
                    st.session_state.user = u
                    st.success("Perfil atualizado!")
            except Exception as e:
                session.rollback()
                st.error(f"Erro: {e}")
            finally:
                session.close()

    # --- ALTERAR SENHA ---
    with tab_senha:
        with st.container(border=True):
            st.subheader("Alterar Senha")
            senha_atual = st.text_input("Senha Atual", type="password", key="cfg_senha_atual")
            nova_senha = st.text_input("Nova Senha", type="password", key="cfg_nova_senha")
            confirmar = st.text_input("Confirmar Nova Senha", type="password", key="cfg_confirmar_senha")

            if st.button("Alterar Senha", key="btn_alterar_senha"):
                if not all([senha_atual, nova_senha, confirmar]):
                    st.error("Preencha todos os campos.")
                elif nova_senha != confirmar:
                    st.error("As senhas não coincidem.")
                else:
                    session = Session()
                    try:
                        u = session.query(UserAnalise).get(user.id)
                        if u and bcrypt.checkpw(senha_atual.encode(), u.password.encode()):
                            u.password = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                            session.commit()
                            st.success("Senha alterada com sucesso!")
                        else:
                            st.error("Senha atual incorreta.")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro: {e}")
                    finally:
                        session.close()

    # --- SISTEMA ---
    with tab_sistema:
        with st.container(border=True):
            st.subheader("Informações do Sistema")
            st.text("Versão: 1.0.0")
            st.text("Framework: Streamlit")
            st.text("Banco de Dados: SQLite")
            st.text("IA: Groq (LLaMA 3.3)")

            st.markdown("---")
            st.subheader("Tema")
            st.caption("O tema pode ser alterado no menu do Streamlit (canto superior direito → Settings → Theme).")

    # --- CARGOS ---
    with tab_cargos:
        with st.container(border=True):
            st.subheader("Cargos do Sistema")
            session = Session()
            try:
                cargos = session.query(Cargo).all()
                import pandas as pd
                df = pd.DataFrame([{"ID": c.id, "Nome": c.nome} for c in cargos])
                st.dataframe(df, use_container_width=True, hide_index=True)
            finally:
                session.close()
