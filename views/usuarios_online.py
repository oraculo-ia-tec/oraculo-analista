"""Página Usuários Online — mostra quem está logado e quem está offline."""

from datetime import datetime, timedelta

import streamlit as st


# Chave do session_state que armazena o dicionário de sessões ativas.
# Formato: { user_id: {"name": str, "email": str, "last_seen": datetime} }
_ONLINE_KEY = "_online_sessions"
_TIMEOUT_MINUTES = 15  # considera offline após N minutos sem atividade


def registrar_sessao_ativa(user_id: int, name: str, email: str):
    """Deve ser chamada a cada página carregada pelo usuário logado."""
    if _ONLINE_KEY not in st.session_state:
        st.session_state[_ONLINE_KEY] = {}
    st.session_state[_ONLINE_KEY][user_id] = {
        "name": name,
        "email": email,
        "last_seen": datetime.now(),
    }


def render_usuarios_online(Session, UserAnalise, Cargo):
    st.header("🟢 Usuários Online / Offline")

    session = Session()
    try:
        usuarios = session.query(UserAnalise).filter_by(is_verified=True).all()
        cargos = {c.id: c.nome for c in session.query(Cargo).all()}
        dados = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "cargo": cargos.get(u.cargo_id, "—"),
            }
            for u in usuarios
        ]
    finally:
        session.close()

    online_sessions: dict = st.session_state.get(_ONLINE_KEY, {})
    agora = datetime.now()
    limite = timedelta(minutes=_TIMEOUT_MINUTES)

    online = []
    offline = []

    for u in dados:
        info = online_sessions.get(u["id"])
        if info and (agora - info["last_seen"]) <= limite:
            online.append({**u, "Último acesso": info["last_seen"].strftime("%H:%M:%S")})
        else:
            last = info["last_seen"].strftime("%d/%m/%Y %H:%M") if info else "—"
            offline.append({**u, "Último acesso": last})

    col_on, col_off = st.columns(2)

    with col_on:
        with st.container(border=True):
            st.subheader(f"🟢 Online ({len(online)})")
            if online:
                import pandas as pd
                df_on = pd.DataFrame(
                    [{"Nome": u["name"], "Email": u["email"], "Cargo": u["cargo"], "Visto às": u["Último acesso"]}
                     for u in online]
                )
                st.dataframe(df_on, width='stretch', hide_index=True)
            else:
                st.info("Nenhum usuário online no momento.")

    with col_off:
        with st.container(border=True):
            st.subheader(f"🔴 Offline ({len(offline)})")
            if offline:
                import pandas as pd
                df_off = pd.DataFrame(
                    [{"Nome": u["name"], "Email": u["email"], "Cargo": u["cargo"], "Último acesso": u["Último acesso"]}
                     for u in offline]
                )
                st.dataframe(df_off, width='stretch', hide_index=True)
            else:
                st.info("Nenhum usuário offline.")

    st.caption(f"Sessão considerada ativa se houve atividade nos últimos {_TIMEOUT_MINUTES} minutos.")
    if st.button("🔄 Atualizar", key="btn_refresh_online"):
        st.rerun()
