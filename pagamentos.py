# ============================================================
# pagamentos.py — Oráculo Analista
# Painel Streamlit de pagamentos (chamado via app.py ou standalone)
# NUNCA chame st.set_page_config() aqui — já feito em app.py
# ============================================================
from __future__ import annotations

import streamlit as st

from src.payments.service import AsaasService
from src.payments.plans import PLANOS, label_preco

_STATUS_OPTS = ["PENDING", "RECEIVED", "CONFIRMED", "OVERDUE"]
_svc = AsaasService()


def render_painel_pagamentos() -> None:
    """Renderiza o painel de pagamentos dentro do app."""
    st.title("💳 Painel de Pagamentos")
    st.divider()

    # ── Listagem ─────────────────────────────────────────
    st.subheader("📊 Cobranças")
    status_sel = st.selectbox(
        "Filtrar por status:",
        options=_STATUS_OPTS,
        format_func=AsaasService.status_pt,
        key="pay_status_filter",
    )

    if st.button("🔄 Atualizar lista", key="pay_refresh"):
        with st.spinner("Buscando cobranças..."):
            try:
                pagamentos = _svc.listar_pagamentos(status_sel)
                if not pagamentos:
                    st.warning("Nenhuma cobrança encontrada.")
                else:
                    import pandas as pd
                    df = pd.DataFrame(pagamentos)
                    colunas = [c for c in ["customer", "value", "billingType", "status", "dueDate", "id"] if c in df.columns]
                    df = df[colunas].rename(columns={
                        "customer":    "Cliente",
                        "value":       "Valor",
                        "billingType": "Tipo",
                        "status":      "Status",
                        "dueDate":     "Vencimento",
                        "id":          "ID",
                    })
                    df["Status"] = df["Status"].apply(AsaasService.status_pt)
                    st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao buscar cobranças: {e}")

    st.divider()

    # ── Verificação manual ──────────────────────────────
    st.subheader("🔍 Verificar pagamento manual")
    payment_id = st.text_input("ID do pagamento Asaas:", key="pay_manual_id")
    if st.button("Verificar", key="pay_manual_btn") and payment_id:
        with st.spinner("Verificando..."):
            try:
                dados = _svc.verificar_pagamento(payment_id)
                status_en = dados.get("status", "")
                st.info(f"Status: **{AsaasService.status_pt(status_en)}**")

                if status_en in ("RECEIVED", "CONFIRMED"):
                    email_cliente = dados.get("customer", "")
                    plano_ativo   = st.selectbox(
                        "Plano a ativar:",
                        options=list(PLANOS.keys()),
                        format_func=label_preco,
                        key="pay_plano_ativar",
                    )
                    if st.button("✅ Ativar plano", key="pay_ativar_btn"):
                        ok = _svc.ativar_plano(email=email_cliente, plano=plano_ativo)
                        if ok:
                            st.success(f"Plano **{label_preco(plano_ativo)}** ativado com sucesso!")
                        else:
                            st.error("Usuário não encontrado no banco.")
            except Exception as e:
                st.error(f"Erro ao verificar: {e}")

    st.divider()

    # ── Criar cobrança manual ────────────────────────────
    with st.expander("➕ Criar cobrança PIX manual", expanded=False):
        c1, c2 = st.columns(2)
        cliente_id = c1.text_input("ID do cliente Asaas:", key="pay_cli_id")
        plano_novo = c2.selectbox(
            "Plano:",
            options=list(PLANOS.keys()),
            format_func=label_preco,
            key="pay_plano_novo",
        )
        if st.button("Gerar cobrança PIX", key="pay_gerar_btn") and cliente_id:
            with st.spinner("Criando cobrança..."):
                try:
                    res = _svc.criar_cobranca_pix(cliente_id, plano_novo)
                    st.success("Cobrança criada!")
                    link = res.get("invoiceUrl") or res.get("bankSlipUrl", "")
                    if link:
                        st.markdown(f"[🔗 Link de pagamento]({link})")
                    st.json(res)
                except Exception as e:
                    st.error(f"Erro: {e}")
