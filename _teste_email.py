"""Teste de envio de e-mail via OAuth2."""
import os
os.chdir('C:/Users/Notebook/oraculo-analista')

import toml
secrets = toml.load('.streamlit/secrets.toml')
email_cfg = secrets.get('email', {})
for k, v in email_cfg.items():
    os.environ[k] = str(v)

from notification import Notificador

n = Notificador()
print('Remetente:', n.sender_email)
print('Refresh token (início):', (n.refresh_token or '')[:40])

try:
    ok = n.enviar_email(
        'oraculoiatec@gmail.com',
        'Teste Oráculo Analista',
        '<h3>Funcionando!</h3><p>E-mail enviado com sucesso via OAuth2.</p>'
    )
    print('Resultado:', ok)
except Exception as e:
    print('ERRO:', e)
