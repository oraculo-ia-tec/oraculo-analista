# ============================================================
# src/sidebar/configuracao.py
# Menu Configuração — Dados, Alterar Senha, Meu Plano
# ============================================================
from __future__ import annotations
import hashlib
import streamlit as st
from ..models.base import Session
from ..models.user import UserAnalise
from ..payments.plans import PLANOS


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def render_configuracao() -> None:
    user = st.session_state.get("user")
    if not user:
        return

    st.title("⚙️ Configuração da Conta")
    tab1, tab2, tab3 = st.tabs(["📝 Dados", "🔒 Alterar Senha", "💳 Meu Plano"])

    with tab1:
        st.subheader("Seus dados cadastrais")
        nome_novo = st.text_input("Nome",     value=user.name,     key="cfg_nome")
        zap_novo  = st.text_input("WhatsApp", value=user.whatsapp, key="cfg_zap")
        st.text_input("E-mail", value=user.email, disabled=True)

        nova_img = st.file_uploader("Foto de perfil (PNG/JPG)", type=["png","jpg","jpeg"], key="cfg_img")
        if nova_img:
            import os
            os.makedirs("./user_profiles/", exist_ok=True)
            ext    = nova_img.name.split(".")[-1]
            caminho = f"./user_profiles/{user.id}_profile.{ext}"
            with open(caminho, "wb") as f:
                f.write(nova_img.read())
            st.image(caminho, width=120)

        if st.button("💾 Salvar dados", key="cfg_salvar"):
            with Session() as session:
                u = session.query(UserAnalise).filter_by(id=user.id).first()
                if u:
                    u.name     = nome_novo
                    u.whatsapp = zap_novo
                    if nova_img:
                        u.profile_image_path = caminho
                    session.commit()
                    st.session_state.user = u
                    st.success("✅ Dados atualizados!")
                    st.rerun()

    with tab2:
        st.subheader("Alterar senha")
        s_atual = st.text_input("Senha atual",     type="password", key="cfg_s_atual")
        s_nova  = st.text_input("Nova senha",      type="password", key="cfg_s_nova")
        s_conf  = st.text_input("Confirmar senha", type="password", key="cfg_s_conf")
        if st.button("🔒 Alterar senha", key="cfg_senha_btn"):
            if not all([s_atual, s_nova, s_conf]):
                st.error("Preencha todos os campos.")
            elif s_nova != s_conf:
                st.error("As senhas não coincidem.")
            elif len(s_nova) < 6:
                st.error("Mínimo 6 caracteres.")
            else:
                with Session() as session:
                    u = session.query(UserAnalise).filter_by(id=user.id).first()
                    if u and u.password == _hash(s_atual):
                        u.password = _hash(s_nova)
                        session.commit()
                        st.success("✅ Senha alterada!")
                    else:
                        st.error("❌ Senha atual incorreta.")

    with tab3:
        st.subheader("Seu plano atual")
        plano  = getattr(user, "plano", "free") or "free"
        venc   = getattr(user, "data_vencimento", None)
        acesso = getattr(user, "acesso_autorizado", False)
        c1, c2, c3 = st.columns(3)
        c1.metric("Plano",      plano.capitalize())
        c2.metric("Vencimento", str(venc) if venc else "—")
        c3.metric("Acesso",     "✅ Ativo" if acesso else "⏳ Pendente")
        st.divider()
        st.markdown("### 🚀 Fazer upgrade")
        for chave, info in PLANOS.items():
            with st.expander(f"{info['label']} — R$ {info['preco']:.2f}"):
                st.write(f"Validade: **{info['dias']} dias**")
                st.link_button(f"💳 Assinar {info['label']}", info["link"])
                if st.button(f"Solicitar upgrade para {chave}", key=f"upg_{chave}"):
                    with Session() as session:
                        u = session.query(UserAnalise).filter_by(id=user.id).first()
                        if u:
                            u.upgrade_solicitado = chave
                            session.commit()
                    st.success(f"✅ Upgrade para **{info['label']}** solicitado!")
