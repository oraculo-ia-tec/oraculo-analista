# ============================================================
# src/payments/plans.py
# Definição centralizada de planos e utilidades de data
# ============================================================
from __future__ import annotations

import datetime

# Planos disponíveis — fonte única de verdade
PLANOS: dict[str, dict] = {
    "mensal": {
        "label":     "Mensal",
        "preco":     49.90,
        "dias":      30,
        "descricao": "Plano Mensal — Oráculo Analista",
        "link":      "https://sandbox.asaas.com/c/qmo94xid8f1i6tnc",
    },
    "trimestral": {
        "label":     "Trimestral",
        "preco":     119.90,
        "dias":      90,
        "descricao": "Plano Trimestral — Oráculo Analista",
        "link":      "https://sandbox.asaas.com/c/jsmak76vdo5fke23",
    },
    "anual": {
        "label":     "Anual",
        "preco":     369.90,
        "dias":      365,
        "descricao": "Plano Anual — Oráculo Analista",
        "link":      "https://sandbox.asaas.com/c/adu6nd24lf8jauo3",
    },
}


def calcular_vencimento(plano: str, inicio: datetime.date | None = None) -> datetime.date:
    """Retorna a data de vencimento com base no plano escolhido."""
    dias = PLANOS.get(plano, {}).get("dias", 30)
    base = inicio or datetime.date.today()
    return base + datetime.timedelta(days=dias)


def label_preco(plano: str) -> str:
    p = PLANOS.get(plano)
    if not p:
        return plano
    return f"{p['label']} — R$ {p['preco']:.2f}"
