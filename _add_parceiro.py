import sqlite3
conn = sqlite3.connect('oraculo_analista.db')
conn.execute("INSERT OR IGNORE INTO cargo (id, nome) VALUES (4, 'Parceiro')")
conn.commit()
print("Cargos:", conn.execute('SELECT * FROM cargo').fetchall())
conn.close()
