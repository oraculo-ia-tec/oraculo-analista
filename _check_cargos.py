import sqlite3
conn = sqlite3.connect('oraculo_analista.db')
c = conn.cursor()
c.execute('SELECT * FROM cargo')
print("Cargos:", c.fetchall())
c.execute('SELECT id, name, email, cargo_id FROM user_analise')
print("Usuarios:", c.fetchall())
conn.close()
