# ============================================================
# pagamentos.py — Oráculo Analista
# Painel Financeiro completo com st.tabs
# ============================================================
from __future__ import annotations
import streamlit as st
from src.payments.service import AsaasService
from src.payments.plans import PLANOS, label_preco

_STATUS_OPTS = ["PENDING", "RECEIVED", "CONFIRMED", "OVERDUE"]
_svc = AsaasService()


def render_painel_pagamentos() -> None:
    st.title("💰 Financeiro")

    tab_lista, tab_verificar, tab_criar, tab_sandbox = st.tabs([
        "📊 Cobranças",
        "🔍 Verificar Pagamento",
        "➕ Criar Cobrança PIX",
        "🧪 Sandbox / Testes",
    ])

    # ── TAB 1 — Listagem ────────────────────────────────
    with tab_lista:
        status_sel = st.selectbox(
            "Filtrar por status:",
            options=_STATUS_OPTS,
            format_func=AsaasService.status_pt,
            key="pay_status_filter",
        )
        if st.button("🔄 Carregar cobranças", key="pay_refresh"):
            with st.spinner("Buscando..."):
                try:
                    pagamentos = _svc.listar_pagamentos(status_sel)
                    if not pagamentos:
                        st.warning("Nenhuma cobrança encontrada.")
                    else:
                        import pandas as pd
                        df = pd.DataFrame(pagamentos)
                        colunas = [c for c in ["customer","value","billingType","status","dueDate","id"] if c in df.columns]
                        df = df[colunas].rename(columns={
                            "customer":"Cliente","value":"Valor","billingType":"Tipo",
                            "status":"Status","dueDate":"Vencimento","id":"ID",
                        })
                        df["Status"] = df["Status"].apply(AsaasService.status_pt)
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ── TAB 2 — Verificar pagamento ──────────────────────
    with tab_verificar:
        payment_id = st.text_input("ID do pagamento Asaas:", key="pay_manual_id")
        if st.button("Verificar", key="pay_manual_btn") and payment_id:
            with st.spinner("Verificando..."):
                try:
                    dados = _svc.verificar_pagamento(payment_id)
                    status_en = dados.get("status", "")
                    st.info(f"Status: **{AsaasService.status_pt(status_en)}**")
                    st.json(dados)

                    if status_en in ("RECEIVED", "CONFIRMED"):
                        plano_ativar = st.selectbox(
                            "Plano a ativar:",
                            options=list(PLANOS.keys()),
                            format_func=label_preco,
                            key="pay_plano_ativar",
                        )
                        email_cli = dados.get("customer", "")
                        if st.button("✅ Ativar plano", key="pay_ativar_btn"):
                            ok = _svc.ativar_plano(email=email_cli, plano=plano_ativar)
                            st.success(f"Plano **{label_preco(plano_ativar)}** ativado!") if ok else st.error("Usuário não encontrado.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ── TAB 3 — Criar cobrança PIX ─────────────────────
    with tab_criar:
        c1, c2 = st.columns(2)
        cliente_id = c1.text_input("ID do cliente Asaas:", key="pay_cli_id")
        plano_novo = c2.selectbox(
            "Plano:",
            options=list(PLANOS.keys()),
            format_func=label_preco,
            key="pay_plano_novo",
        )
        nome_cli  = st.text_input("Nome do cliente", key="pay_nome_cli")
        email_cli = st.text_input("E-mail do cliente", key="pay_email_cli")
        fone_cli  = st.text_input("WhatsApp (somente números)", key="pay_fone_cli")

        col_a, col_b = st.columns(2)
        if col_a.button("Criar cliente Asaas", key="pay_criar_cli") and nome_cli:
            try:
                res = _svc.criar_cliente(nome_cli, email_cli, fone_cli)
                st.success(f"Cliente criado! ID: **{res.get('id')}**")
            except Exception as e:
                st.error(f"Erro: {e}")

        if col_b.button("Gerar cobrança PIX", key="pay_gerar_btn") and cliente_id:
            try:
                res = _svc.criar_cobranca_pix(cliente_id, plano_novo)
                st.success("Cobrança criada!")
                link = res.get("invoiceUrl") or res.get("bankSlipUrl", "")
                if link:
                    st.markdown(f"[🔗 Link de pagamento]({link})")
                st.json(res)
            except Exception as e:
                st.error(f"Erro: {e}")

    # ── TAB 4 — Sandbox / Testes ───────────────────────
    with tab_sandbox:
        st.info("🧪 Ambiente de testes — Asaas Sandbox")
        st.markdown("""Use os dados abaixo para simular pagamentos no ambiente sandbox:
- **PIX:** qualquer chave aleatória
- **Cartão:** `5162306219378829` CVV `318` Val `05/2027`
- **Boleto:** gera o boleto e pague pelo painel Asaas Sandbox
        """)
        st.divider()
        st.subheader("📋 Simular confirmação de pagamento")
        sim_email = st.text_input("E-mail do usuário:", key="sim_email")
        sim_plano = st.selectbox("Plano:", list(PLANOS.keys()), format_func=label_preco, key="sim_plano")
        if st.button("✅ Confirmar pagamento (simulação)", key="sim_confirmar"):
            if sim_email:
                ok = _svc.ativar_plano(email=sim_email, plano=sim_plano)
                st.success(f"Plano **{label_preco(sim_plano)}** ativado para `{sim_email}`!") if ok else st.error("❌ Usuário não encontrado.")
            else:
                st.warning("Informe o e-mail.")
