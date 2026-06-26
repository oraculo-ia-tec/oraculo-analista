# 🔮 Oráculo Analista — Design System v2.0

Design system completo para o app Streamlit.

---

## Estrutura de arquivos

```
.streamlit/
  config.toml               ← Tema Streamlit: dark, gold primary, superfícies escuras

ui/
  __init__.py               ← Exports centralizados
  tokens.py                 ← Paleta de cores, espaçamentos, raios (referência Python)
  styles.py                 ← CSS global + inject_global_styles()
  components.py             ← Todos os wrappers de componentes reutilizáveis
```

---

## Como usar

### 1. Inicializar o Design System no app

No início de `app.py` (antes de qualquer `st.*`):

```python
from ui import inject_global_styles

def main():
    inject_global_styles()   # ← apenas aqui, uma vez
    # ... resto da lógica ...
```

### 2. Usar os componentes

```python
from ui import hero_header, divider, empty_state, render_badge

hero_header(title="Oráculo Analista", subtitle="Transformando dados em decisões")
divider(gold=True)
render_badge("PDF carregado", kind="success")
empty_state(icon="🔮", title="Sem documentos", description="Envie um arquivo para começar.")
```

---

## Componentes disponíveis

| Componente | Substitui |
|---|---|
| `inject_global_styles()` | CSS inline espalhado |
| `hero_header(title, subtitle)` | `.titulo-principal` inline |
| `section_header(label)` | `st.subheader` + CSS |
| `sidebar_brand(name)` | `st.sidebar.title` |
| `card(title, content_html)` | Divs soltas |
| `feature_card(icon, title, desc)` | Colunas com markdown |
| `divider(gold=False)` | `st.markdown("---")` |
| `render_badge(label, kind)` | Emojis inline |
| `empty_state(icon, title, desc)` | Ausente |
| `upload_panel(...)` | `st.sidebar.file_uploader` puro |
| `user_profile_block(...)` | `st.sidebar.write` manual |
| `landing_feature_grid(features)` | 6 `st.columns` repetidos |
| `landing_cta_button(label)` | `st.button` puro |
| `footer(credits)` | `<small><center>` |
| `dialog_info_decorator(title)` | `st.dialog` bruto |

---

## Design Tokens

| Token CSS | Valor | Uso |
|---|---|---|
| `--gold` | `#C9A84C` | Acento primário, CTAs, bordas de destaque |
| `--bg` | `#0D0D0F` | Fundo principal |
| `--surface` | `#141417` | Sidebar, containers |
| `--surface-2` | `#1A1A1F` | Cards, inputs |
| `--text` | `#E8E6E1` | Texto principal |
| `--text-muted` | `#9896A0` | Descrições, labels |

---

## Regras obrigatórias

1. **`inject_global_styles()` UMA vez** — no início do `main()` de `app.py`
2. **Nunca duplicar bordas** — o container organiza, o componente interno não repete
3. **Alertas ao usuário → `st.dialog`** — nunca mensagens inline soltas
4. **Gradiente violeta → descontinuado** — substituído por gold gradient
5. **Componentes nativos têm prioridade** — HTML só quando nativo não entrega

---

Desenvolvido por Oráculos IA · Design System v2.0 · Junho/2026
