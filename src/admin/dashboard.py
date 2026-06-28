# ============================================================
# src/admin/dashboard.py
# Dashboard Admin — métricas de uso, tokens, custos e usuários
# ============================================================
from __future__ import annotations

import datetime

import streamlit as st
from sqlalchemy import func

from ..models.base import Session
from ..models.user import UserAnalise, Cargo
from ..constants.settings import (
    APP_NAME,
    COST_PER_1M_INPUT_TOKENS,
    COST_PER_1M_OUTPUT_TOKENS,
    MAX_TOKENS_FREE_PLAN,
    MAX_TOKENS_PRO_PLAN,
)


# ── helpers ────────────────────────────────────────────────
def _is_admin(user) -> bool:
    """Verifica se o usuário logado tem cargo de admin."""
    if not user:
        return False
    nome_cargo = getattr(user, "_cargo_nome", "").lower()
    return any(k in nome_cargo for k in ("admin", "gestor", "master", "dev"))


def _carregar_usuarios() -> list:
    with Session() as session:
        try:
            rows = (
                session.query(UserAnalise, Cargo.nome)
                .outerjoin(Cargo, UserAnalise.cargo_id == Cargo.id)
                .all()
            )
            result = []
            for u, cargo_nome in rows:
                u._cargo_nome = cargo_nome or "—"
                result.append(u)
            return result
        except Exception:
            return []


def _metricas_sessao() -> dict:
    """Lê métricas de tokens da sessão atual (CostHook)."""
    hook = st.session_state.get("_cost_hook")
    if hook and hasattr(hook, "summary"):
        return hook.summary()
    return {
        "calls": st.session_state.get("_total_calls", 0),
        "input_tokens": st.session_state.get("_input_tokens", 0),
        "output_tokens": st.session_state.get("_output_tokens", 0),
        "total_tokens": st.session_state.get("_total_tokens", 0),
        "cost_usd": st.session_state.get("_cost_usd", 0.0),
    }


# ── seções do dashboard ────────────────────────────────────
def _secao_kpis(usuarios: list) -> None:
    total       = len(usuarios)
    verificados = sum(1 for u in usuarios if u.is_verified)
    pendentes   = total - verificados
    taxa_conv   = round((verificados / total * 100), 1) if total else 0.0

    st.markdown("### 👥 Usuários")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total cadastrados", total)
    c2.metric("✅ Verificados",    verificados)
    c3.metric("⏳ Pendentes",     pendentes)
    c4.metric("Taxa de conversão", f"{taxa_conv}%")


def _secao_tokens(metricas: dict) -> None:
    st.markdown("### 🤖 Tokens & Custo da Sessão")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chamadas ao LLM",  metricas["calls"])
    c2.metric("Tokens entrada",   f"{metricas['input_tokens']:,}")
    c3.metric("Tokens saída",     f"{metricas['output_tokens']:,}")
    c4.metric("💰 Custo USD",     f"${metricas['cost_usd']:.4f}")

    total_tok = metricas["total_tokens"]
    if total_tok > 0:
        pct_free = min(total_tok / MAX_TOKENS_FREE_PLAN * 100, 100)
        pct_pro  = min(total_tok / MAX_TOKENS_PRO_PLAN  * 100, 100)
        st.caption(f"Plano Free: {pct_free:.0f}% usado ({MAX_TOKENS_FREE_PLAN:,} tok limite)")
        st.progress(int(pct_free))
        st.caption(f"Plano Pro: {pct_pro:.0f}% usado ({MAX_TOKENS_PRO_PLAN:,} tok limite)")
        st.progress(int(pct_pro))


def _secao_custo_projetado(metricas: dict) -> None:
    st.markdown("### 📈 Projeção de Custo Mensal")
    custo_sessao = metricas["cost_usd"]
    if custo_sessao <= 0:
        st.info("Nenhuma chamada ao LLM nesta sessão ainda.")
        return

    # Estima custo por dia baseado na sessão atual
    hora_atual = datetime.datetime.now().hour or 1
    custo_hora = custo_sessao / hora_atual
    c1, c2, c3 = st.columns(3)
    c1.metric("Custo desta sessão",  f"${custo_sessao:.4f}")
    c2.metric("Estimativa / dia",    f"${custo_hora * 24:.3f}")
    c3.metric("Estimativa / mês",    f"${custo_hora * 24 * 30:.2f}")

    st.caption(
        f"💡 Baseado em: entrada ${COST_PER_1M_INPUT_TOKENS}/1M tok · "
        f"saída ${COST_PER_1M_OUTPUT_TOKENS}/1M tok (Groq llama-3.3-70b)"
    )


def _secao_lista_usuarios(usuarios: list) -> None:
    st.markdown("### 📋 Lista de Usuários")

    # Filtros
    col_f1, col_f2 = st.columns([3, 1])
    busca  = col_f1.text_input("🔍 Buscar por nome ou e-mail", key="admin_busca")
    apenas = col_f2.selectbox("Filtrar", ["Todos", "Verificados", "Pendentes"], key="admin_filtro")

    filtrado = usuarios
    if busca:
        busca_lower = busca.lower()
        filtrado = [
            u for u in filtrado
            if busca_lower in u.name.lower() or busca_lower in u.email.lower()
        ]
    if apenas == "Verificados":
        filtrado = [u for u in filtrado if u.is_verified]
    elif apenas == "Pendentes":
        filtrado = [u for u in filtrado if not u.is_verified]

    if not filtrado:
        st.warning("Nenhum usuário encontrado.")
        return

    rows = []
    for u in filtrado:
        rows.append({
            "ID":          u.id,
            "Nome":        u.name,
            "E-mail":      u.email,
            "WhatsApp":    u.whatsapp,
            "Cargo":       getattr(u, "_cargo_nome", "—"),
            "Verificado":  "✅" if u.is_verified else "⏳",
        })

    st.dataframe(rows, use_container_width=True)
    st.caption(f"Exibindo {len(rows)} de {len(usuarios)} usuários.")


def _secao_atividade_recente() -> None:
    """Mostra últimas consultas ao LLM na sessão."""
    audit = st.session_state.get("_audit_log", [])
    if not audit:
        st.info("Nenhuma atividade registrada nesta sessão.")
        return

    st.markdown("### 📜 Atividade Recente (sessão)")
    for entrada in reversed(audit[-10:]):
        ts      = entrada.get("ts", "")[:19].replace("T", " ")
        resumo  = str(entrada.get("prompt", ""))[:80]
        tokens  = entrada.get("total_tokens", "—")
        st.markdown(f"- `{ts}` · **{tokens} tok** · _{resumo}..._")


# ── render principal ───────────────────────────────────────
def render_dashboard() -> None:
    """
    Ponto de entrada do Dashboard Admin.
    Chamado apenas para usuários com cargo admin/gestor.
    """
    st.title(f"📊 Dashboard Admin — {APP_NAME}")
    st.caption(f"Sessão iniciada em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    usuarios = _carregar_usuarios()
    metricas = _metricas_sessao()

    _secao_kpis(usuarios)
    st.divider()
    _secao_tokens(metricas)
    st.divider()
    _secao_custo_projetado(metricas)
    st.divider()
    _secao_lista_usuarios(usuarios)
    st.divider()
    _secao_atividade_recente()

    with st.expander("⚙️ Configurações do sistema", expanded=False):
        from ..constants.settings import DEFAULT_MODEL, MAX_CONTEXT_CHARS, MAX_HISTORY_MESSAGES
        st.json({
            "modelo":             DEFAULT_MODEL,
            "max_context_chars":  MAX_CONTEXT_CHARS,
            "max_history_msgs":   MAX_HISTORY_MESSAGES,
            "custo_input_1M":     f"${COST_PER_1M_INPUT_TOKENS}",
            "custo_output_1M":    f"${COST_PER_1M_OUTPUT_TOKENS}",
        })
