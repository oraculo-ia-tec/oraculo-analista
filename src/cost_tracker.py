# ============================================================
# src/cost_tracker.py
# Wrapper de sessão para CostHook — integrado ao Streamlit
# ============================================================
import streamlit as st
from .hooks.cost_hook import CostHook


def get_cost_tracker() -> CostHook:
    if "_cost_hook" not in st.session_state:
        st.session_state["_cost_hook"] = CostHook()
    return st.session_state["_cost_hook"]


def reset_cost_tracker() -> None:
    if "_cost_hook" in st.session_state:
        st.session_state["_cost_hook"].reset()


def render_cost_widget() -> None:
    hook = get_cost_tracker()
    summary = hook.summary()
    if summary["calls"] == 0:
        return
    with st.sidebar.expander("📊 Uso da sessão", expanded=False):
        st.metric("Tokens consumidos", f"{summary['total_tokens']:,}")
        st.metric("Chamadas ao LLM",   summary["calls"])
        st.metric("Custo estimado",    f"$ {summary['cost_usd']:.5f}")
