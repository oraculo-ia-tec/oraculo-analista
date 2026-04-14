"""
Menu interativo para teste de envio de e-mail com templates personalizados do Oráculo Analista.
Testa todos os templates disponíveis no sistema de notificação.
"""
from notification import Notificador


EMAIL_TESTE = "rededescpro@gmail.com"
NOME_TESTE = "Usuário Teste"
WHATSAPP_TESTE = "11999999999"


def menu():
    print("\n" + "=" * 60)
    print("   ORÁCULO ANALISTA — Teste de Envio de E-mail")
    print("=" * 60)
    print(f"   Destinatário: {EMAIL_TESTE}")
    print("-" * 60)
    print("  1. Boas-vindas (template completo com logo)")
    print("  2. Código de Verificação (template com código)")
    print("  3. Confirmação de Agendamento")
    print("  4. Confirmação de Pagamento")
    print("  5. E-mail genérico personalizado")
    print("  6. Enviar TODOS os templates")
    print("  0. Sair")
    print("-" * 60)
    return input("  Escolha uma opção: ").strip()


def enviar_boas_vindas(notificador):
    print("\n>> Enviando e-mail de Boas-vindas...")
    try:
        notificador.enviar_boas_vindas(
            nome=NOME_TESTE,
            email=EMAIL_TESTE,
            whatsapp=WHATSAPP_TESTE,
            cargo="Cliente",
        )
        print("   ✅ E-mail de Boas-vindas enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        return False


def enviar_verificacao(notificador):
    print("\n>> Enviando e-mail de Verificação...")
    try:
        notificador.enviar_verificacao(
            nome=NOME_TESTE,
            email=EMAIL_TESTE,
            codigo="482613",
        )
        print("   ✅ E-mail de Verificação enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        return False


def enviar_agendamento(notificador):
    print("\n>> Enviando e-mail de Confirmação de Agendamento...")
    try:
        notificador.enviar_confirmacao_agendamento(
            nome=NOME_TESTE,
            email=EMAIL_TESTE,
            data="20/04/2026",
            hora="14:00",
        )
        print("   ✅ E-mail de Agendamento enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        return False


def enviar_pagamento(notificador):
    print("\n>> Enviando e-mail de Confirmação de Pagamento...")
    try:
        notificador.enviar_confirmacao_pagamento(
            nome=NOME_TESTE,
            email=EMAIL_TESTE,
            plano="Mensal (R$ 49,90)",
        )
        print("   ✅ E-mail de Pagamento enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        return False


def enviar_generico(notificador):
    print("\n>> Enviando e-mail genérico personalizado...")
    assunto = "Teste de Template — Oráculo Analista"
    html = """
    <div style="background:#0d0d1a;padding:40px;font-family:'Segoe UI',Arial,sans-serif;">
      <div style="max-width:600px;margin:0 auto;background:linear-gradient(160deg,#1a1a2e,#16213e);
                  border-radius:16px;border:1px solid #3a1f6e;overflow:hidden;">
        <div style="padding:36px 32px;text-align:center;">
          <h1 style="margin:0;font-size:26px;font-weight:700;
                     background:linear-gradient(90deg,#a855f7,#ffffff);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Oráculo Analista
          </h1>
          <p style="color:#b0aac8;font-size:15px;margin:10px 0 0;">
            Teste de e-mail personalizado
          </p>
        </div>
        <div style="padding:0 32px 24px;">
          <p style="font-size:16px;line-height:1.6;color:#d0c8e8;">
            Olá, <strong style="color:#a855f7;">Usuário Teste</strong>! 👋
          </p>
          <p style="font-size:14px;line-height:1.7;color:#c4b8de;">
            Este é um <strong>e-mail de teste genérico</strong> do sistema Oráculo Analista.
            Se você está recebendo este e-mail, significa que a integração com a
            <strong>API do Gmail (OAuth2)</strong> está funcionando corretamente.
          </p>
          <div style="background:#1a103a;border-radius:10px;border:1px solid #3730a3;padding:16px 20px;margin:16px 0;">
            <p style="margin:0;font-size:14px;color:#c4b5fd;font-weight:700;">
              ✅ Sistema de e-mail operacional
            </p>
            <ul style="margin:8px 0 0;padding-left:20px;font-size:14px;line-height:1.8;color:#b0aac8;">
              <li>OAuth2 autenticado com sucesso</li>
              <li>Gmail API respondendo normalmente</li>
              <li>Templates HTML renderizados corretamente</li>
            </ul>
          </div>
        </div>
        <div style="padding:20px 32px;background:#0a0a1a;border-top:1px solid #2d1b69;text-align:center;">
          <p style="margin:0;font-size:12px;color:#4b5563;">
            © 2026 Oráculo Analista — Desenvolvido com ❤️ por Oráculos AI
          </p>
        </div>
      </div>
    </div>
    """
    try:
        notificador.enviar_email(EMAIL_TESTE, assunto, html)
        print("   ✅ E-mail genérico enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        return False


def enviar_todos(notificador):
    print("\n>> Enviando TODOS os templates...")
    resultados = {
        "Boas-vindas": enviar_boas_vindas(notificador),
        "Verificação": enviar_verificacao(notificador),
        "Agendamento": enviar_agendamento(notificador),
        "Pagamento": enviar_pagamento(notificador),
        "Genérico": enviar_generico(notificador),
    }
    print("\n" + "=" * 60)
    print("   RESUMO DO ENVIO")
    print("=" * 60)
    for template, ok in resultados.items():
        status = "✅ OK" if ok else "❌ FALHA"
        print(f"   {template:.<40} {status}")
    print("=" * 60)


def main():
    notificador = Notificador()

    acoes = {
        "1": lambda: enviar_boas_vindas(notificador),
        "2": lambda: enviar_verificacao(notificador),
        "3": lambda: enviar_agendamento(notificador),
        "4": lambda: enviar_pagamento(notificador),
        "5": lambda: enviar_generico(notificador),
        "6": lambda: enviar_todos(notificador),
    }

    while True:
        opcao = menu()
        if opcao == "0":
            print("\n   Saindo do teste de e-mail. Até mais!\n")
            break
        acao = acoes.get(opcao)
        if acao:
            acao()
        else:
            print("\n   ⚠️  Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
