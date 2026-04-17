"""Página Dashboard — métricas e gráficos modernos com Seaborn."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime

# ── Paleta dark/violeta ──────────────────────────────────────────────────────
_BG        = "#0d0d1a"
_PANEL     = "#13132b"
_BORDER    = "#3a1f6e"
_PURPLE    = "#a855f7"
_BLUE      = "#3b82f6"
_GREEN     = "#22c55e"
_AMBER     = "#f59e0b"
_RED       = "#ef4444"
_TEXT      = "#e2e8f0"
_SUBTEXT   = "#94a3b8"

_PALETTE   = [_PURPLE, _BLUE, _GREEN, _AMBER, _RED, "#06b6d4", "#ec4899"]

def _apply_dark_style(fig, ax_list):
    """Aplica tema dark/violeta a todos os axes de uma figura."""
    fig.patch.set_facecolor(_BG)
    for ax in (ax_list if isinstance(ax_list, (list, tuple)) else [ax_list]):
        ax.set_facecolor(_PANEL)
        ax.tick_params(colors=_SUBTEXT, labelsize=9)
        ax.xaxis.label.set_color(_SUBTEXT)
        ax.yaxis.label.set_color(_SUBTEXT)
        ax.title.set_color(_TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(_BORDER)


def render_dashboard(Session, UserAnalise, Cargo):
    # ── CSS inline ────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .dash-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(90deg, #a855f7, #3b82f6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: .25rem;
    }
    .dash-sub { font-size: .9rem; color: #64748b; margin-bottom: 1.5rem; }
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #3a1f6e; border-radius: 14px;
        padding: 1.2rem 1.5rem; text-align: center;
    }
    .kpi-label { font-size: .75rem; text-transform: uppercase;
                 letter-spacing: 1.5px; color: #64748b; margin-bottom: .3rem; }
    .kpi-value { font-size: 2.4rem; font-weight: 800; color: #e2e8f0; line-height: 1; }
    .kpi-delta { font-size: .8rem; margin-top: .3rem; }
    .section-title {
        font-size: 1.05rem; font-weight: 700; color: #a855f7;
        letter-spacing: .5px; margin: 1.5rem 0 .75rem;
        border-left: 3px solid #a855f7; padding-left: .6rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="dash-title">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="dash-sub">Atualizado em {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}</p>',
        unsafe_allow_html=True,
    )

    # ── Dados ─────────────────────────────────────────────────────────────────
    session = Session()
    try:
        usuarios  = session.query(UserAnalise).all()
        cargos    = {c.id: c.nome for c in session.query(Cargo).all()}
        dados_usuarios = [
            {
                "Nome":      u.name,
                "Email":     u.email,
                "Cargo":     cargos.get(u.cargo_id, "—"),
                "Verificado": u.is_verified,
            }
            for u in usuarios
        ]
    finally:
        session.close()

    df              = pd.DataFrame(dados_usuarios) if dados_usuarios else pd.DataFrame()
    total           = len(dados_usuarios)
    verificados     = sum(1 for u in dados_usuarios if u["Verificado"])
    pendentes       = total - verificados
    pct_verif       = round(verificados / total * 100) if total else 0

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        (c1, "👥 Total de Usuários", total,       "#a855f7"),
        (c2, "✅ Verificados",       verificados,  "#22c55e"),
        (c3, "⏳ Pendentes",         pendentes,    "#f59e0b"),
        (c4, "📈 Taxa Verificação",  f"{pct_verif}%", "#3b82f6"),
    ]
    for col, label, value, color in kpis:
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{color};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if df.empty:
        st.info("Nenhum usuário cadastrado ainda.")
        return

    # ── Linha 1: Distribuição por cargo  +  Verificados vs Pendentes ──────────
    st.markdown('<p class="section-title">Distribuição de Usuários</p>', unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        cargo_counts = df["Cargo"].value_counts()
        colors_bar   = _PALETTE[:len(cargo_counts)]

        fig, ax = plt.subplots(figsize=(6, 3.2))
        _apply_dark_style(fig, ax)

        bars = ax.bar(cargo_counts.index, cargo_counts.values,
                      color=colors_bar, width=0.55, edgecolor=_BORDER, linewidth=0.8)

        # Rótulos nas barras
        for bar, val in zip(bars, cargo_counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    str(val), ha="center", va="bottom",
                    color=_TEXT, fontsize=10, fontweight="bold")

        ax.set_title("Usuários por Cargo", fontsize=11, pad=10, color=_TEXT, fontweight="bold")
        ax.set_ylabel("Quantidade", fontsize=9)
        ax.set_ylim(0, cargo_counts.max() + 1.5)
        ax.grid(axis="y", color=_BORDER, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_right:
        labels  = ["Verificados", "Pendentes"]
        sizes   = [verificados if verificados else 0.001, pendentes if pendentes else 0.001]
        colors  = [_GREEN, _AMBER]
        explode = (0.05, 0)

        fig2, ax2 = plt.subplots(figsize=(4, 3.2))
        _apply_dark_style(fig2, ax2)

        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, colors=colors, explode=explode,
            autopct="%1.0f%%", startangle=90,
            wedgeprops=dict(edgecolor=_BG, linewidth=2),
            textprops=dict(color=_TEXT, fontsize=9),
        )
        for at in autotexts:
            at.set_color(_BG)
            at.set_fontweight("bold")

        ax2.set_title("Verificação de Contas", fontsize=11, pad=8, color=_TEXT, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Linha 2: Heatmap de cargos x verificação  +  Tabela ───────────────────
    st.markdown('<p class="section-title">Análise Detalhada</p>', unsafe_allow_html=True)
    col_heat, col_table = st.columns([2, 3])

    with col_heat:
        pivot = (
            df.assign(Status=df["Verificado"].map({True: "Verificado", False: "Pendente"}))
              .groupby(["Cargo", "Status"])
              .size()
              .unstack(fill_value=0)
        )
        # Garante colunas mesmo com dados parciais
        for col_name in ["Verificado", "Pendente"]:
            if col_name not in pivot.columns:
                pivot[col_name] = 0

        fig3, ax3 = plt.subplots(figsize=(4, max(2.5, len(pivot) * 0.8 + 1)))
        _apply_dark_style(fig3, ax3)

        cmap = sns.light_palette(_PURPLE, as_cmap=True)
        sns.heatmap(
            pivot, annot=True, fmt="d", cmap=cmap,
            linewidths=0.5, linecolor=_BG,
            ax=ax3, cbar=False,
            annot_kws={"size": 11, "weight": "bold", "color": _BG},
        )
        ax3.set_title("Cargo × Status", fontsize=11, pad=8, color=_TEXT, fontweight="bold")
        ax3.set_xlabel("")
        ax3.set_ylabel("")
        ax3.tick_params(axis="x", colors=_TEXT, labelsize=9)
        ax3.tick_params(axis="y", colors=_TEXT, labelsize=9, rotation=0)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    with col_table:
        st.markdown("**Todos os usuários**")
        df_display = df.copy()
        df_display["Verificado"] = df_display["Verificado"].map({True: "✅", False: "⏳"})
        st.dataframe(
            df_display[["Nome", "Email", "Cargo", "Verificado"]],
            width="stretch",
            hide_index=True,
            height=220,
        )

    # ── Linha 3: Barras horizontais por cargo (seaborn) ───────────────────────
    if len(df["Cargo"].unique()) > 1:
        st.markdown('<p class="section-title">Ranking por Cargo</p>', unsafe_allow_html=True)

        fig4, ax4 = plt.subplots(figsize=(8, max(2.5, len(cargo_counts) * 0.7 + 1)))
        _apply_dark_style(fig4, ax4)

        df_rank = pd.DataFrame({"Cargo": cargo_counts.index, "Total": cargo_counts.values})
        df_rank["cor"] = [_PALETTE[i % len(_PALETTE)] for i in range(len(df_rank))]
        palette_map = dict(zip(df_rank["Cargo"], df_rank["cor"]))
        sns.barplot(
            data=df_rank, x="Total", y="Cargo", hue="Cargo",
            palette=palette_map, ax=ax4, orient="h",
            edgecolor=_BORDER, linewidth=0.6, legend=False,
        )

        for i, val in enumerate(cargo_counts.values):
            ax4.text(val + 0.05, i, str(val),
                     va="center", color=_TEXT, fontsize=10, fontweight="bold")

        ax4.set_title("Total de usuários por cargo", fontsize=11, pad=8, color=_TEXT, fontweight="bold")
        ax4.set_xlabel("Quantidade", fontsize=9)
        ax4.set_xlim(0, cargo_counts.max() + 1.5)
        ax4.grid(axis="x", color=_BORDER, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close(fig4)
