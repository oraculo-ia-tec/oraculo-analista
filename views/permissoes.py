"""Mapa de permissões por cargo."""

# Páginas disponíveis por cargo (nome do cargo -> lista de páginas)
PERMISSOES = {
    "Desenvolvedor de IA": [
        "Oráculo Analista",
        "Dashboard",
        "Clientes",
        "Parceiros",
        "Financeiro",
        "Configuração",
    ],
    "Admin": [
        "Oráculo Analista",
        "Dashboard",
        "Clientes",
        "Parceiros",
        "Financeiro",
        "Configuração",
    ],
    "Parceiro": [
        "Oráculo Analista",
        "Dashboard",
        "Clientes",
    ],
    "Cliente": [
        "Oráculo Analista",
    ],
}


def obter_paginas_por_cargo(cargo_nome: str) -> list[str]:
    """Retorna a lista de páginas permitidas para o cargo informado."""
    return PERMISSOES.get(cargo_nome, ["Oráculo Analista"])
