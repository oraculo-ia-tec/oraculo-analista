"""
Registra / atualiza William Eustaquio Gomes da Silva
como Desenvolvedor de IA no banco de dados local.
"""

import sqlite3
import bcrypt

DB = 'oraculo_analista.db'

NOME     = 'William Eustaquio Gomes da Silva'
EMAIL    = 'oraculoiatec@gmail.com'
WHATSAPP = '998417976'
SENHA    = 'william2026'
CARGO_ID = 1   # Desenvolvedor de IA

senha_hash = bcrypt.hashpw(SENHA.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect(DB)
cur  = conn.cursor()

cur.execute('SELECT id FROM user_analise WHERE email = ?', (EMAIL,))
row = cur.fetchone()

if row:
    cur.execute(
        '''
        UPDATE user_analise
           SET name             = ?,
               whatsapp         = ?,
               password         = ?,
               is_verified      = 1,
               cargo_id         = ?,
               verification_code = NULL
         WHERE email = ?
        ''',
        (NOME, WHATSAPP, senha_hash, CARGO_ID, EMAIL),
    )
    print(f'[OK] Usuário atualizado — ID {row[0]}')
else:
    cur.execute(
        '''
        INSERT INTO user_analise (name, whatsapp, email, password, is_verified, cargo_id)
        VALUES (?, ?, ?, ?, 1, ?)
        ''',
        (NOME, WHATSAPP, EMAIL, senha_hash, CARGO_ID),
    )
    print(f'[OK] Usuário criado — ID {cur.lastrowid}')

conn.commit()

cur.execute(
    'SELECT id, name, email, whatsapp, is_verified, cargo_id '
    'FROM user_analise WHERE email = ?',
    (EMAIL,),
)
r = cur.fetchone()
conn.close()

print()
print('=== Registro salvo ===')
print(f'  ID          : {r[0]}')
print(f'  Nome        : {r[1]}')
print(f'  E-mail      : {r[2]}')
print(f'  WhatsApp    : {r[3]}')
print(f'  Verificado  : {"Sim" if r[4] else "Não"}')
print(f'  Cargo ID    : {r[5]}  (Desenvolvedor de IA)')
