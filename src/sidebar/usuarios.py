# ============================================================
# src/sidebar/usuarios.py
# Menu Usuários — somente Desenvolvedor de IA
# ============================================================
from __future__ import annotations
import datetime
import streamlit as st
from ..models.base import Session
from ..models.user import UserAnalise, Cargo

DEV_CARGOS = {"dev", "desenvolvedor", "desenvolvedor de ia", "admin", "master"}


def _cargo_nome(user) -> str:
    try:
        with Session() as session:
            c = session.query(Cargo).filter_by(id=user.cargo_id).first()
            return c.nome.lower() if c else ""
    except Exception:
        return ""


def tem_acesso_usuarios(user) -> bool:
    if not user:
        return False
    return any(d in _cargo_nome(user) for d in DEV_CARGOS)


def render_usuarios() -> None:
    st.title("👥 Monitor de Usuários")

    tab_todos, tab_pendentes, tab_online, tab_sessoes = st.tabs([
        "📊 Todos", "⏳ Não verificados", "🟢 Online agora", "🕐 Sessões"
    ])

    # Carrega todos os usuários
    with Session() as session:
        try:
            rows = (
                session.query(UserAnalise, Cargo.nome)
                .outerjoin(Cargo, UserAnalise.cargo_id == Cargo.id)
                .all()
            )
            usuarios = []
            for u, cargo_nome in rows:
                usuarios.append({
                    "ID":          u.id,
                    "Nome":        u.name,
                    "E-mail":      u.email,
                    "WhatsApp":    u.whatsapp,
                    "Cargo":       cargo_nome or "—",
                    "Verificado":  "✅" if u.is_verified else "⏳",
                    "Plano":       getattr(u, "plano", "free"),
                    "Cadastro":    str(getattr(u, "created_at", "—")),
                })
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {e}")
            return

    # Sessões ativas (armazenadas em st.session_state global via dicionário)
    sessoes_ativas: dict = st.session_state.get("_sessoes_ativas", {})
    user_atual = st.session_state.get("user")
    if user_atual:
        uid = str(user_atual.id)
        if uid not in sessoes_ativas:
            sessoes_ativas[uid] = {
                "nome":   user_atual.name,
                "email":  user_atual.email,
                "inicio": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "fim":    "—",
            }
            st.session_state["_sessoes_ativas"] = sessoes_ativas

    import pandas as pd

    with tab_todos:
        st.caption(f"{len(usuarios)} usuários cadastrados")
        busca = st.text_input("🔍 Buscar", key="usr_busca")
        dados = [u for u in usuarios if not busca or busca.lower() in u["Nome"].lower() or busca.lower() in u["E-mail"].lower()]
        st.dataframe(dados, use_container_width=True)

    with tab_pendentes:
        pendentes = [u for u in usuarios if u["Verificado"] == "⏳"]
        st.caption(f"{len(pendentes)} usuários não verificados")
        if pendentes:
            st.dataframe(pendentes, use_container_width=True)
        else:
            st.success("✅ Todos os usuários estão verificados!")

    with tab_online:
        online = list(sessoes_ativas.values())
        st.caption(f"{len(online)} sessões ativas")
        if online:
            st.dataframe(online, use_container_width=True)
        else:
            st.info("Nenhuma sessão ativa registrada.")

    with tab_sessoes:
        st.caption("Histórico de sessões desta execução")
        hist = st.session_state.get("_historico_sessoes", [])
        if hist:
            st.dataframe(hist, use_container_width=True)
        else:
            st.info("Nenhum histórico de sessão ainda.")
