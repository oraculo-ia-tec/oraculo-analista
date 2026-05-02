"""Página Banco de Dados — diagnóstico e exportação de todos os usuários."""

import io
import os

import pandas as pd
import streamlit as st


def render_banco_dados(Session, UserAnalise, Cargo, database_url: str = ""):
    st.markdown("""
    <style>
    .bd-title {
        font-size: 1.8rem; font-weight: 800;
        background: linear-gradient(90deg, #a855f7, #3b82f6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: .2rem;
    }
    .bd-badge {
        display: inline-block; padding: .25rem .75rem;
        border-radius: 999px; font-size: .75rem; font-weight: 700;
        letter-spacing: .5px; text-transform: uppercase;
    }
    .bd-badge-sqlite { background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; }
    .bd-badge-pg     { background: #14532d; color: #86efac; border: 1px solid #22c55e; }
    .bd-warn {
        background: #451a03; border: 1px solid #f59e0b;
        border-radius: 10px; padding: .75rem 1rem;
        font-size: .85rem; color: #fcd34d; margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="bd-title">🗄️ Banco de Dados</p>', unsafe_allow_html=True)

    # ── Diagnóstico do banco em uso ──────────────────────────────────────────
    db_url = database_url or os.getenv("DATABASE_URL", "sqlite:///oraculo_analista.db")
    is_sqlite = db_url.startswith("sqlite")
    badge_cls = "bd-badge-sqlite" if is_sqlite else "bd-badge-pg"
    badge_txt = "SQLite (local/efêmero)" if is_sqlite else "PostgreSQL (nuvem)"

    st.markdown(
        f'<span class="bd-badge {badge_cls}">{badge_txt}</span>',
        unsafe_allow_html=True,
    )
    st.caption(f"URL em uso: `{db_url[:60]}{'...' if len(db_url) > 60 else ''}`")

    if is_sqlite:
        st.markdown("""
        <div class="bd-warn">
        ⚠️ <strong>Atenção:</strong> você está usando SQLite. No Streamlit Cloud o arquivo de banco
        é <strong>efêmero</strong> — os dados podem ser perdidos a cada redeploy.<br/>
        O banco local (<code>oraculo_analista.db</code>) e o banco do Streamlit Cloud são
        <strong>arquivos separados e independentes</strong>. Usuários cadastrados em um ambiente
        não aparecem no outro. Recomenda-se migrar para PostgreSQL (ex: Supabase) para dados persistentes e compartilhados.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Consulta todos os usuários ───────────────────────────────────────────
    session = Session()
    try:
        usuarios = session.query(UserAnalise).all()
        cargos   = {c.id: c.nome for c in session.query(Cargo).all()}
        dados = [
            {
                "ID":          u.id,
                "Nome":        u.name,
                "Email":       u.email,
                "WhatsApp":    u.whatsapp,
                "Cargo":       cargos.get(u.cargo_id, "—"),
                "Verificado":  "✅" if u.is_verified else "⏳ Pendente",
                "Imagem":      "Sim" if u.profile_image_path else "Não",
            }
            for u in usuarios
        ]
    finally:
        session.close()

    df = pd.DataFrame(dados) if dados else pd.DataFrame()

    # ── KPIs rápidos ─────────────────────────────────────────────────────────
    total      = len(dados)
    verif      = sum(1 for d in dados if "✅" in d["Verificado"])
    pendentes  = total - verif

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de usuários", total)
    c2.metric("✅ Verificados",     verif)
    c3.metric("⏳ Pendentes",       pendentes)

    st.markdown("---")

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        busca = st.text_input("🔍 Buscar por nome ou e-mail", key="bd_busca", placeholder="Digite...")
    with col_f2:
        opcoes_cargo = ["Todos"] + sorted({d["Cargo"] for d in dados})
        filtro_cargo = st.selectbox("Cargo", opcoes_cargo, key="bd_cargo")
    with col_f3:
        filtro_verif = st.selectbox("Status", ["Todos", "✅ Verificados", "⏳ Pendentes"], key="bd_verif")

    if not df.empty:
        df_filtrado = df.copy()
        if busca:
            mask = (
                df_filtrado["Nome"].str.contains(busca, case=False, na=False) |
                df_filtrado["Email"].str.contains(busca, case=False, na=False)
            )
            df_filtrado = df_filtrado[mask]
        if filtro_cargo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Cargo"] == filtro_cargo]
        if filtro_verif == "✅ Verificados":
            df_filtrado = df_filtrado[df_filtrado["Verificado"] == "✅"]
        elif filtro_verif == "⏳ Pendentes":
            df_filtrado = df_filtrado[df_filtrado["Verificado"] == "⏳ Pendente"]

        st.markdown(f"**{len(df_filtrado)} usuário(s) encontrado(s)**")
        st.dataframe(df_filtrado, width='stretch', hide_index=True)

        # ── Exportar CSV ─────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Exportar")
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            csv = df_filtrado.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Baixar CSV (filtrado)",
                data=csv,
                file_name="usuarios_filtrados.csv",
                mime="text/csv",
                key="btn_dl_filtrado",
            )
        with col_exp2:
            csv_all = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Baixar CSV (todos)",
                data=csv_all,
                file_name="todos_usuarios.csv",
                mime="text/csv",
                key="btn_dl_todos",
            )
    else:
        st.info("Nenhum usuário encontrado neste banco de dados.")
