import sqlite3
conn = sqlite3.connect('oraculo_analista.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tabelas:", tables)
for t in tables:
    cursor.execute(f"PRAGMA table_info({t})")
    cols = cursor.fetchall()
    print(f"\n{t}:")
    for c in cols:
        print(f"  {c}")
conn.close()
