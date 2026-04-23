"""Página Automação — configurações de notificação de novos cadastros por e-mail."""

import threading

import streamlit as st

# Chave para armazenar a configuração de automação na sessão/estado persistente
_AUTO_KEY = "_automacao_cfg"


def _cfg() -> dict:
    if _AUTO_KEY not in st.session_state:
        st.session_state[_AUTO_KEY] = {
            "ativo": False,
            "destinatarios": "",
            "log": [],
        }
    return st.session_state[_AUTO_KEY]


def notificar_novo_usuario(name: str, email: str, cargo: str, notificador_cls):
    """
    Chamada no momento do cadastro para disparar e-mail de notificação aos
    administradores, se a automação estiver ativa.
    """
    cfg = _cfg()
    if not cfg.get("ativo"):
        return

    destinatarios = [d.strip() for d in cfg.get("destinatarios", "").split(",") if d.strip()]
    if not destinatarios:
        return

    def _enviar():
        for dest in destinatarios:
            try:
                n = notificador_cls()
                n.enviar_notificacao_novo_usuario(name, email, cargo, dest)
            except Exception as exc:
                cfg["log"].append(f"❌ Erro ao notificar {dest}: {exc}")
            else:
                cfg["log"].append(f"✅ Notificação enviada para {dest} sobre novo usuário '{name}' ({email})")

    threading.Thread(target=_enviar, daemon=True).start()


def render_automacao(Session, UserAnalise, Cargo):
    st.header("🤖 Automação")

    cfg = _cfg()

    # --- Ativar/desativar ---
    with st.container(border=True):
        st.subheader("Notificação de Novo Cadastro")
        st.write(
            "Quando ativado, um e-mail de notificação será disparado para os "
            "destinatários abaixo sempre que um novo usuário se cadastrar no sistema."
        )

        ativo = st.toggle(
            "Ativar notificação por e-mail",
            value=cfg["ativo"],
            key="auto_toggle",
        )
        cfg["ativo"] = ativo

        destinatarios = st.text_area(
            "E-mails dos destinatários (separados por vírgula)",
            value=cfg["destinatarios"],
            key="auto_dest",
            placeholder="admin@empresa.com, devIA@empresa.com",
            height=80,
        )
        cfg["destinatarios"] = destinatarios

        if st.button("💾 Salvar configuração", key="btn_save_auto"):
            st.success("Configuração salva com sucesso!")

    st.markdown("---")

    # --- Teste manual ---
    with st.container(border=True):
        st.subheader("Testar Notificação")
        st.caption("Envia um e-mail de teste para verificar se a configuração está correta.")

        col1, col2 = st.columns(2)
        with col1:
            email_teste = st.text_input("E-mail de teste", key="auto_email_teste",
                                        placeholder="seu@email.com")
        with col2:
            st.write("")
            st.write("")
            if st.button("📧 Enviar teste", key="btn_auto_teste"):
                if not email_teste:
                    st.error("Informe um e-mail de destino para o teste.")
                else:
                    try:
                        from notification import Notificador
                        n = Notificador()
                        n.enviar_notificacao_novo_usuario(
                            "Usuário Teste",
                            "teste@oraculo.ai",
                            "Cliente",
                            email_teste,
                        )
                        cfg["log"].append(f"✅ E-mail de teste enviado para {email_teste}")
                        st.success(f"E-mail de teste enviado para {email_teste}!")
                    except Exception as exc:
                        cfg["log"].append(f"❌ Falha no teste para {email_teste}: {exc}")
                        st.error(f"Erro ao enviar: {exc}")

    st.markdown("---")

    # --- Log de eventos ---
    with st.container(border=True):
        st.subheader("📋 Log de Notificações")
        if cfg["log"]:
            for entry in reversed(cfg["log"][-50:]):  # últimas 50
                st.write(entry)
        else:
            st.info("Nenhuma notificação registrada ainda.")

        if st.button("🗑️ Limpar log", key="btn_clear_log"):
            cfg["log"] = []
            st.rerun()

    # --- Resumo de cadastros recentes ---
    with st.container(border=True):
        st.subheader("👤 Últimos Cadastros")
        session = Session()
        try:
            usuarios = session.query(UserAnalise).order_by(UserAnalise.id.desc()).limit(10).all()
            cargos = {c.id: c.nome for c in session.query(Cargo).all()}
            dados = [
                {
                    "Nome": u.name,
                    "Email": u.email,
                    "Cargo": cargos.get(u.cargo_id, "—"),
                    "Verificado": "✅" if u.is_verified else "⏳",
                }
                for u in usuarios
            ]
        finally:
            session.close()

        if dados:
            import pandas as pd
            st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum usuário cadastrado.")
