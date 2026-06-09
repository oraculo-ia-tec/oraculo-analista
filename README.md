# 🔮 Oráculo Analista

> Agente de IA para análise inteligente de documentos — PDF, Excel, CSV e muito mais.
> Arquitetura inspirada no Claude Code: loop agêntico, sistema de tools, memória persistente e hooks de segurança.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/LLM-Groq%20%2F%20llama--3.3--70b-green.svg)](https://groq.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## ✨ O que é

O **Oráculo Analista** é um assistente de IA que roda no navegador (via Streamlit) e permite que qualquer usuário — sem saber programar — faça perguntas em linguagem natural sobre documentos complexos.

```
Usuário: "Qual foi o produto mais vendido em março?"
Oráculo: [lê o Excel] → [calcula] → "O produto A liderou com 3.200 unidades, +18% vs fevereiro."
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py (Streamlit)                    │
│          Login → Upload → Chat com streaming                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                     Runtime (1 por sessão)
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
    QueryEngine        HookChain          CostTracker
    (loop agêntico)   (permissão,         (tokens + R$)
          │            custo, audit)
          │
    ┌─────┴──────┐
    │  Tool Pool │  ← 8+ ferramentas
    └─────┬──────┘
          │
    ┌─────┴───────────────────────────────────┐
    │  tool_pdf  tool_excel  tool_calculator   │
    │  tool_csv  tool_chart  tool_web_search   │
    │  tool_export_pdf  tool_memory_write      │
    └─────────────────────────────────────────┘
          │
    MemoryManager  ←  MEMORY.md por usuário
    SessionStore   ←  histórico de sessões
```

---

## 🚀 Instalação rápida

### 1. Clone o repositório

```bash
git clone https://github.com/oraculo-ia-tec/oraculo-analista.git
cd oraculo-analista
```

### 2. Crie o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env e adicione sua GROQ_API_KEY
```

> Obtenha sua chave gratuita em: https://console.groq.com

### 5. Inicie o app

```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

---

## 🔑 Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GROQ_API_KEY` | ✅ Sim | Chave da API Groq (LLM) |
| `SERPAPI_KEY` | ⬜ Opcional | Habilita `tool_web_search` |
| `SUPABASE_URL` | ⬜ Opcional | Auth em produção |
| `SUPABASE_ANON_KEY` | ⬜ Opcional | Auth em produção |

---

## 🧰 Tools disponíveis

| Tool | Plano | Descrição |
|---|---|---|
| `tool_calculator` | 🆓 Free | Calculadora segura (sem `eval` direto) |
| `tool_pdf` | 🆓 Free | Leitura e extração de PDF |
| `tool_csv` | 🆓 Free | Análise de arquivos CSV |
| `tool_excel` | ⭐ Pro | Leitura de planilhas Excel |
| `tool_chart_generator` | ⭐ Pro | Geração de gráficos Plotly |
| `tool_web_search` | ⭐ Pro | Busca na web via SerpAPI |
| `tool_export_pdf` | ⭐ Pro | Exporta respostas em PDF |
| `tool_memory_write` | 🆓 Free | Salva informações na memória do usuário |

---

## 🔐 Sistema de Permissões

Configurado em `settings.json`:

```json
{
  "permissions": {
    "file_read":  "allow",
    "file_write": "ask",
    "web_search": "allow",
    "export":     "allow",
    "delete":     "deny"
  }
}
```

Valores possíveis: `allow` | `ask` | `deny`

---

## 🧪 Rodando os testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=term-missing

# Módulo específico
pytest tests/test_tools.py -v
pytest tests/test_memory.py -v
pytest tests/test_hooks.py -v
```

---

## 📁 Estrutura do projeto

```
oraculo-analista/
├── app.py                    # Interface Streamlit (entrada principal)
├── settings.json             # Permissões do sistema
├── requirements.txt          # Dependências Python
├── pytest.ini               # Configuração de testes
├── .env.example             # Template de variáveis de ambiente
│
├── src/
│   ├── runtime.py           # Orquestrador de sessão
│   ├── query_engine.py      # Loop agêntico (pensa → age → responde)
│   ├── query_engine_factory.py
│   ├── cost_tracker.py      # Monitora custo de tokens
│   ├── permissions.py       # Lê settings.json
│   │
│   ├── tools/               # 8+ ferramentas
│   │   ├── tool_calculator.py
│   │   ├── tool_pdf.py
│   │   ├── tool_excel.py
│   │   ├── tool_csv.py
│   │   ├── tool_chart_generator.py
│   │   ├── tool_web_search.py
│   │   ├── tool_export_pdf.py
│   │   └── tool_memory_write.py
│   │
│   ├── hooks/               # Middleware de segurança
│   │   ├── base.py          # BaseHook + HookChain
│   │   ├── permission_hook.py
│   │   ├── cost_hook.py
│   │   └── audit_hook.py
│   │
│   ├── memory/              # Memória persistente
│   │   ├── memory_manager.py
│   │   └── session_store.py
│   │
│   ├── types/               # Tipos e dataclasses
│   │   └── base.py
│   │
│   └── utils/
│       └── helpers.py
│
└── tests/
    ├── conftest.py
    ├── test_tools.py
    ├── test_memory.py
    ├── test_hooks.py
    └── test_cost_tracker.py
```

---

## ☁️ Deploy no Streamlit Cloud

1. Faça fork ou push deste repositório para seu GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório e selecione `app.py` como entry point
4. Em **Secrets**, adicione:
   ```toml
   GROQ_API_KEY = "sua_chave_aqui"
   ```
5. Clique em **Deploy** ✅

---

## 🗺️ Roadmap

- [ ] Autenticação com Supabase Auth
- [ ] Planos com Stripe
- [ ] Suporte a imagens (visão computacional)
- [ ] Tool para banco de dados SQL
- [ ] Modo multi-documento (comparar arquivos)
- [ ] API REST pública
- [ ] Exportação para Google Sheets

---

## 📄 Licença

MIT © 2026 Oráculo IA Tec
