import sqlite3

conn = sqlite3.connect('oraculo_analista.db')
conn.execute("INSERT INTO cargo (id, nome) VALUES (1, 'Desenvolvedor de IA')")
conn.execute("INSERT INTO cargo (id, nome) VALUES (2, 'Admin')")
conn.execute("INSERT INTO cargo (id, nome) VALUES (3, 'Cliente')")
conn.execute("INSERT INTO cargo (id, nome) VALUES (4, 'Parceiro')")
conn.commit()
print('Cargos recriados:', conn.execute(
    'SELECT id, nome FROM cargo').fetchall())
conn.close()
