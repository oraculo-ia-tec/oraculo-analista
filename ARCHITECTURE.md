# 🏛️ Arquitetura Claude Code — Oráculo Analista v2.0

Documento técnico de referência da implementação da Arquitetura Claude Code no Oráculo Analista.

---

## 📐 Visão Geral

```
┌─────────────────────────────────────────────────────────┐
│                    app.py (Streamlit UI)                 │
└────────────────────────┬────────────────────────────────┘
                         │ input do usuário
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   runtime.py                            │
│         (gerencia ciclo de vida da sessão)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 query_engine.py                         │
│     ┌──────────────────────────────────────────────┐    │
│     │         LOOP AGÊNTICO (while)                │    │
│     │                                              │    │
│     │  1. Injeta contexto + memória do usuário     │    │
│     │  2. Chama API Groq                           │    │
│     │  3. Se tool_call → executa tool              │    │
│     │  4. Adiciona resultado ao histórico          │    │
│     │  5. Volta ao passo 2 até resposta final      │    │
│     └──────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌─────────────────────┐   ┌───────────────────────────┐
│    tools/           │   │   memory/                  │
│  ├ tool_pdf.py      │   │  ├ memory_manager.py       │
│  ├ tool_excel.py    │   │  └ session_store.py        │
│  ├ tool_email.py    │   └───────────────────────────┘
│  ├ tool_asaas.py    │
│  └ tool_txt.py      │
└─────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                   hooks/ + permissions.py               │
│         (intercepta TODA execução de tool)              │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Diretórios

```
oraculo-analista/
├── app.py                    # UI Streamlit (adaptada)
├── analista.py               # Motor de análise (adaptado)
├── ARCHITECTURE.md           # Este arquivo
├── requirements.txt
│
├── src/                      # ← NOVO: toda a arquitetura
│   ├── types/                # Tipos e dataclasses base
│   │   └── base.py
│   ├── constants/            # Constantes globais
│   │   └── settings.py
│   ├── utils/                # Funções utilitárias
│   │   └── helpers.py
│   ├── state/                # Store global (singleton)
│   │   └── store.py
│   ├── schemas/              # Validadores de input
│   │   └── validators.py
│   ├── tools/                # ← PARTE 2
│   │   ├── base.py
│   │   ├── tool_pool.py
│   │   ├── tool_pdf.py
│   │   ├── tool_excel.py
│   │   ├── tool_email.py
│   │   ├── tool_asaas.py
│   │   └── tool_txt.py
│   ├── memory/               # ← PARTE 3
│   │   ├── memory_manager.py
│   │   └── session_store.py
│   ├── query_engine.py       # ← PARTE 4
│   ├── hooks/                # ← PARTE 5
│   │   └── cost_hook.py
│   ├── permissions.py        # ← PARTE 5
│   └── runtime.py            # ← PARTE 6
│
├── user_profiles/            # Memória persistente por usuário
│   └── {user_id}/
│       └── MEMORY.md
│
└── tests/                    # ← PARTE 7
    ├── test_tools.py
    ├── test_memory.py
    └── test_query_engine.py
```

---

## 🔄 Fluxo de uma Requisição

1. Usuário digita pergunta no chat Streamlit
2. `app.py` chama `runtime.run(user_input, session)`
3. `runtime.py` valida input e despacha para `query_engine`
4. `query_engine` injeta: `system_prompt + memoria_usuario + historico + documento_ativo`
5. Loop agêntico começa: chama Groq → verifica tool_calls
6. Para cada tool_call: `permissions.check()` → `hooks.before()` → `tool.execute()` → `hooks.after()`
7. Resultado da tool é adicionado ao histórico e Groq é chamado novamente
8. Quando Groq retorna resposta final (sem tool_calls): loop encerra
9. `runtime` atualiza memória do usuário via `memory_manager`
10. Resposta final exibida no chat

---

## 🧠 Sistema de Memória

Cada usuário possui um arquivo `user_profiles/{user_id}/MEMORY.md` com:
- Histórico de documentos analisados
- Preferências identificadas
- Contexto de sessões anteriores
- Insights salvos pelo próprio sistema

---

## 🔐 Segurança

- Chaves de API **nunca** no repositório — usar `.env` local
- `secrets.toml` adicionado ao `.gitignore`
- Sistema `allow/deny/ask` por tool e por plano
- Hooks auditam toda execução de tool

---

*Implementado em 7 partes incrementais — Arquitetura Claude Code v2.0*
