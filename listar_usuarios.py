import sqlite3

DB_PATH = "oraculo_analista.db"


def listar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Usuários em user_analise:")
    try:
        cur.execute(
            "SELECT id, name, email, whatsapp, is_verified FROM user_analise")
        for row in cur.fetchall():
            print(row)
    except Exception as e:
        print("Erro ao consultar user_analise:", e)

    print("\nUsuários em user_admin:")
    try:
        cur.execute(
            "SELECT id, name, email, whatsapp, decisao as is_verified FROM user_admin")
        for row in cur.fetchall():
            print(row)
    except Exception as e:
        print("Erro ao consultar user_admin:", e)

    conn.close()


if __name__ == "__main__":
    listar_usuarios()
