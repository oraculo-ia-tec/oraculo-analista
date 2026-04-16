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
        "Usuários Online",
        "Automação",
    ],
    "Admin": [
        "Oráculo Analista",
        "Dashboard",
        "Clientes",
        "Parceiros",
        "Financeiro",
        "Configuração",
        "Usuários Online",
        "Automação",
    ],
    "Parceiro": [
        "Oráculo Analista",
        "Dashboard",
        "Clientes",
        "Configuração",
    ],
    "Cliente": [
        "Oráculo Analista",
        "Configuração",
    ],
}


def obter_paginas_por_cargo(cargo_nome: str) -> list[str]:
    """Retorna a lista de páginas permitidas para o cargo informado."""
    return PERMISSOES.get(cargo_nome, ["Oráculo Analista"])
