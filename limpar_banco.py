import sqlite3

conn = sqlite3.connect('oraculo_analista.db')

# Listar tabelas
tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
print('Tabelas encontradas:')
for t in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
    print(f'  {t}: {count} registros')

# Limpar dados de todas as tabelas
for t in tables:
    conn.execute(f'DELETE FROM [{t}]')
    print(f'  -> {t} limpa')

conn.commit()
conn.close()
print('\nTodos os dados foram removidos com sucesso!')
