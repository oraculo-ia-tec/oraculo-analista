import sqlite3

conn = sqlite3.connect('oraculo_analista.db')
conn.execute("UPDATE user_analise SET name = 'William Eustaquio' WHERE id = 1")
conn.execute("UPDATE user_analise SET name = 'Tony Stark' WHERE id = 2")
conn.commit()

rows = conn.execute('SELECT id, name, email FROM user_analise').fetchall()
for r in rows:
    print(f'ID: {r[0]} | Nome: {r[1]} | Email: {r[2]}')
conn.close()
