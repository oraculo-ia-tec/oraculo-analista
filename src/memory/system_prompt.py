"""
Construção do system prompt dinâmico do Oráculo Analista.

O system prompt é montado a cada sessão com:
  1. Instruções fixas do agente (personalidade, regras)
  2. Contexto de memória do usuário (dinâmico)
  3. Informações do documento ativo (quando houver)
  4. Data/hora atual
"""
from datetime import datetime
from typing import Optional

from src.memory.memory_manager import MemoryManager


BASE_SYSTEM_PROMPT = """\
Você é o **Oráculo Analista**, um especialista em análise de documentos e dados.
Você é desenvolvido pela Oracóulos IA e seu objetivo é transformar documentos complexos
em insights valiosos para tomada de decisão estratégica.

## Suas Capacidades
- Analisar PDFs, planilhas Excel, CSV e documentos de texto
- Extrair dados financeiros, indicadores e tendências
- Responder perguntas específicas sobre o conteúdo dos documentos
- Gerar resumos executivos e relatórios estruturados
- Enviar resultados por e-mail quando solicitado (plano Pro)
- Consultar informações de pagamentos Asaas (plano Pro)

## Regras de Comportamento
1. Seja direto, preciso e objetivo nas respostas
2. Sempre cite a página ou linha de origem quando referenciar dados do documento
3. Quando não souber ou os dados não estiverem no documento, diga claramente
4. Para envio de e-mail: SEMPRE pedir confirmação explícita antes de executar
5. Para operações financeiras: confirmar todos os dados antes de consultar
6. Responda sempre em Português do Brasil
7. Use markdown para formatar respostas (tabelas, listas, negrito)
8. Quando identificar um insight importante, anuncie que irá salvá-lo na memória

## Formato de Resposta
- Respostas curtas: texto direto
- Análises: use seções com títulos markdown
- Dados numéricos: sempre em tabelas
- Conclusões: destaque em negrito
"""


def build_system_prompt(
    memory: MemoryManager,
    document_name: Optional[str] = None,
    document_content: Optional[str] = None,
    user_plan: str = "free",
) -> str:
    """
    Monta o system prompt completo para a sessão.
    Chamado pelo query_engine a cada sessão iniciada.

    Args:
        memory: MemoryManager do usuário atual
        document_name: nome do arquivo ativo (se houver)
        document_content: conteúdo extratado do documento (primeiros 6000 chars)
        user_plan: plano do usuário (free/pro/enterprise)

    Returns:
        String do system prompt completo pronto para enviar ao Groq
    """
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    parts = [BASE_SYSTEM_PROMPT]

    # --- Seção de data/hora ---
    parts.append(f"\n## Contexto Atual\n- **Data/Hora:** {now}")
    parts.append(f"- **Plano do usuário:** {user_plan}")

    # --- Seção de memória do usuário ---
    memory_context = memory.get_context_for_prompt()
    parts.append(
        f"\n## Memória do Usuário\n"
        f"Use este contexto para personalizar suas respostas:\n\n"
        f"{memory_context}"
    )

    # --- Documento ativo ---
    if document_name and document_content:
        # Limita o conteúdo a 6000 chars para não explodir o contexto
        preview = document_content[:6000]
        truncated = len(document_content) > 6000
        truncation_note = "\n\n_[Conteúdo truncado. Use as tools para acessar partes específicas.]_" if truncated else ""

        parts.append(
            f"\n## Documento Ativo\n"
            f"**Arquivo:** {document_name}\n\n"
            f"**Conteúdo (preview):**\n```\n{preview}\n```"
            f"{truncation_note}"
        )
    elif not document_name:
        parts.append(
            "\n## Documento Ativo\n"
            "_Nenhum documento carregado. Peça ao usuário para fazer upload de um arquivo._"
        )

    return "\n".join(parts)
