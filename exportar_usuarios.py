"""
Exporta todos os usuários cadastrados (user_analise e user_admin)
para o arquivo usuarios_cadastrados.txt.
"""

import sqlite3
from datetime import datetime

DB_PATH = "oraculo_analista.db"
OUTPUT_FILE = "usuarios_cadastrados.txt"


def exportar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    linhas = []
    linha_sep = "=" * 60
    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    linhas.append(linha_sep)
    linhas.append("   ORÁCULO ANALISTA — LISTA DE USUÁRIOS CADASTRADOS")
    linhas.append(f"   Gerado em: {gerado_em}")
    linhas.append(linha_sep)

    # ── user_analise ──────────────────────────────────────────
    linhas.append("\n[ TABELA: user_analise ]\n")
    try:
        cur.execute(
            "SELECT id, name, email, whatsapp, is_verified, cargo_id "
            "FROM user_analise ORDER BY id"
        )
        rows = cur.fetchall()
        if rows:
            for row in rows:
                linhas.append(f"  ID          : {row[0]}")
                linhas.append(f"  Nome        : {row[1]}")
                linhas.append(f"  E-mail      : {row[2]}")
                linhas.append(f"  WhatsApp    : {row[3]}")
                linhas.append(f"  Verificado  : {'Sim' if row[4] else 'Não'}")
                linhas.append(f"  Cargo ID    : {row[5]}")
                linhas.append("-" * 40)
        else:
            linhas.append("  Nenhum usuário encontrado.")
    except Exception as e:
        linhas.append(f"  Erro ao consultar user_analise: {e}")

    # ── user_admin ────────────────────────────────────────────
    linhas.append("\n[ TABELA: user_admin ]\n")
    try:
        cur.execute(
            "SELECT id, name, email, whatsapp, decisao, cargo_id, "
            "created_at, cidade, estado_civil "
            "FROM user_admin ORDER BY id"
        )
        rows = cur.fetchall()
        if rows:
            for row in rows:
                linhas.append(f"  ID           : {row[0]}")
                linhas.append(f"  Nome         : {row[1]}")
                linhas.append(f"  E-mail       : {row[2]}")
                linhas.append(f"  WhatsApp     : {row[3]}")
                linhas.append(f"  Ativo        : {'Sim' if row[4] else 'Não'}")
                linhas.append(f"  Cargo ID     : {row[5]}")
                linhas.append(f"  Cadastro em  : {row[6]}")
                linhas.append(f"  Cidade       : {row[7]}")
                linhas.append(f"  Estado civil : {row[8]}")
                linhas.append("-" * 40)
        else:
            linhas.append("  Nenhum usuário encontrado.")
    except Exception as e:
        linhas.append(f"  Erro ao consultar user_admin: {e}")

    linhas.append("\n" + linha_sep)
    conn.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"Arquivo '{OUTPUT_FILE}' gerado com sucesso.")


if __name__ == "__main__":
    exportar_usuarios()
