"""
Query Engine — Oráculo Analista v2.0

Núcleo da Arquitetura Claude Code: implementa o loop agêntico
que permite ao LLM executar múltiplas tools em sequência até
chegar a uma resposta final.

Fluxo:
  1. Recebe input do usuário + SessionState
  2. Monta system prompt dinâmico com memória do usuário
  3. Chama Groq com lista de tools disponíveis
  4. Se resposta tem tool_calls → executa via ToolPool
  5. Adiciona resultado ao histórico e volta ao passo 3
  6. Quando Groq retorna sem tool_calls → retorna resposta final
"""
import json
import os
from typing import Generator, Optional

from groq import Groq

from src.constants.settings import (
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    MAX_TOKENS_PER_MESSAGE,
    MAX_TOOL_CALLS_PER_SESSION,
)
from src.memory.memory_manager import MemoryManager
from src.memory.system_prompt import build_system_prompt
from src.tools.base import ToolRegistry
from src.tools.tool_pool import ToolPool
from src.types.base import Message, MessageRole, SessionState, ToolCall, ToolResult
from src.utils.helpers import generate_id, estimate_tokens


class QueryEngine:
    """
    Motor de consulta com loop agêntico.
    Uma instância por sessão do usuário.
    """

    def __init__(self, session: SessionState, memory: MemoryManager):
        self.session = session
        self.memory = memory
        self.tool_pool = ToolPool()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        self._tool_calls_this_turn = 0

    # ─── Método principal ────────────────────────────────────────────────────────────

    def run(self, user_input: str) -> str:
        """
        Executa o loop agêntico completo para um input do usuário.
        Retorna a resposta final como string.

        Loop:
          while True:
            resposta = chamar_groq()
            se tem tool_calls: executar tools e continuar
            senão: retornar resposta final
        """
        self._tool_calls_this_turn = 0

        # 1. Adiciona mensagem do usuário ao histórico
        user_message = Message(
            role=MessageRole.USER,
            content=user_input,
        )
        self.session.add_message(user_message)

        # 2. Monta system prompt com memória do usuário
        system_prompt = build_system_prompt(
            memory=self.memory,
            document_name=self.session.active_document,
            document_content=self.session.document_content,
            user_plan=self.session.user.plan,
        )

        # 3. Obtém tools disponíveis para o plano do usuário
        tools_schemas = ToolRegistry.get_schemas_for_plan(self.session.user.plan)

        # 4. LOOP AGÊNTICO
        while True:
            # Verifica limite de tool calls para evitar loops infinitos
            if self._tool_calls_this_turn >= MAX_TOOL_CALLS_PER_SESSION:
                return (
                    "⚠️ Limite de operações por sessão atingido. "
                    "Por favor, inicie uma nova conversão."
                )

            # Chama o Groq
            response = self._call_groq(
                system_prompt=system_prompt,
                tools=tools_schemas,
            )

            if response is None:
                return "❌ Erro ao conectar com o modelo de IA. Tente novamente."

            choice = response.choices[0]
            message = choice.message

            # Registra tokens usados
            if response.usage:
                tokens = response.usage.total_tokens
                self.session.total_tokens += tokens
                self.session.user.total_tokens_used += tokens

            # 5. Verifica se o modelo quer executar tools
            if choice.finish_reason == "tool_calls" and message.tool_calls:
                # Adiciona a mensagem do assistente com tool_calls ao histórico
                self.session.messages.append(
                    Message(
                        role=MessageRole.ASSISTANT,
                        content=message.content or "",
                    )
                )

                # Executa cada tool call
                for tc in message.tool_calls:
                    tool_result = self._execute_tool(tc)

                    # Adiciona resultado da tool ao histórico no formato Groq
                    tool_msg = Message(
                        role=MessageRole.TOOL,
                        content=json.dumps(
                            tool_result.to_dict(),
                            ensure_ascii=False
                        ),
                    )
                    self.session.add_message(tool_msg)
                    self._tool_calls_this_turn += 1
                    self.session.tool_calls_count += 1

                # Continua o loop (Groq processa o resultado das tools)
                continue

            # 6. Sem tool_calls: resposta final
            final_response = message.content or ""

            # Adiciona resposta final ao histórico
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=final_response,
            )
            self.session.add_message(assistant_message)

            # Auto-save de insight se a resposta for substancial
            if len(final_response) > 200 and self.session.active_document:
                self._maybe_save_insight(final_response)

            return final_response

    def run_stream(self, user_input: str) -> Generator[str, None, None]:
        """
        Versão streaming do loop agêntico.
        Yield de chunks de texto para exibição em tempo real no Streamlit.
        Tools são executadas de forma transparente (sem interromper o stream).
        """
        self._tool_calls_this_turn = 0

        user_message = Message(role=MessageRole.USER, content=user_input)
        self.session.add_message(user_message)

        system_prompt = build_system_prompt(
            memory=self.memory,
            document_name=self.session.active_document,
            document_content=self.session.document_content,
            user_plan=self.session.user.plan,
        )
        tools_schemas = ToolRegistry.get_schemas_for_plan(self.session.user.plan)

        # Primeira chamada sem stream para checar tool_calls
        # (Groq não suporta streaming + tool_calls simultaneamente)
        response = self._call_groq(system_prompt=system_prompt, tools=tools_schemas)
        if response is None:
            yield "❌ Erro ao conectar com o modelo de IA."
            return

        choice = response.choices[0]
        message = choice.message

        # Processa tool_calls normalmente
        while choice.finish_reason == "tool_calls" and message.tool_calls:
            if self._tool_calls_this_turn >= MAX_TOOL_CALLS_PER_SESSION:
                yield "\n⚠️ Limite de operações atingido."
                return

            self.session.messages.append(
                Message(role=MessageRole.ASSISTANT, content=message.content or "")
            )

            for tc in message.tool_calls:
                yield f"\n🔧 Executando: `{tc.function.name}`..."
                tool_result = self._execute_tool(tc)
                status_emoji = "✅" if tool_result.success else "❌"
                yield f" {status_emoji}\n"

                tool_msg = Message(
                    role=MessageRole.TOOL,
                    content=json.dumps(tool_result.to_dict(), ensure_ascii=False),
                )
                self.session.add_message(tool_msg)
                self._tool_calls_this_turn += 1
                self.session.tool_calls_count += 1

            response = self._call_groq(system_prompt=system_prompt, tools=tools_schemas)
            if response is None:
                yield "❌ Erro ao reconectar com o modelo."
                return
            choice = response.choices[0]
            message = choice.message

        # Stream da resposta final
        final_response = message.content or ""
        self.session.add_message(
            Message(role=MessageRole.ASSISTANT, content=final_response)
        )

        # Yield da resposta em chunks para efeito de digitação
        chunk_size = 30
        for i in range(0, len(final_response), chunk_size):
            yield final_response[i:i + chunk_size]

        if len(final_response) > 200 and self.session.active_document:
            self._maybe_save_insight(final_response)

    # ─── Métodos internos ─────────────────────────────────────────────────────────

    def _call_groq(self, system_prompt: str, tools: list) -> Optional[object]:
        """
        Chama a API Groq com o histórico completo da sessão.
        Tenta o modelo principal, cai para fallback em caso de erro de quota.
        """
        messages = self._build_messages_for_groq(system_prompt)

        for model in [DEFAULT_MODEL, FALLBACK_MODEL]:
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": MAX_TOKENS_PER_MESSAGE,
                    "temperature": 0.3,
                }
                # Só inclui tools se houver tools disponíveis
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self.client.chat.completions.create(**kwargs)
                return response

            except Exception as e:
                error_str = str(e).lower()
                # Se for erro de quota/rate limit, tenta o fallback
                if "rate_limit" in error_str or "quota" in error_str:
                    continue
                # Outros erros: retorna None
                return None

        return None

    def _build_messages_for_groq(self, system_prompt: str) -> list:
        """
        Monta a lista de mensagens no formato Groq.
        System prompt como primeira mensagem, depois o histórico da sessão.
        Aplica compressão de contexto se o histórico estiver muito longo.
        """
        messages = [{"role": "system", "content": system_prompt}]

        history = self.session.messages

        # Compressão: se o histórico tiver mais de 30 mensagens,
        # mantém as 5 primeiras (contexto inicial) + as 20 mais recentes
        if len(history) > 30:
            history = history[:5] + history[-20:]

        for msg in history:
            groq_msg: dict = {"role": msg.role.value, "content": msg.content}

            # Mensagens de tool precisam de tool_call_id
            if msg.role == MessageRole.TOOL:
                groq_msg["tool_call_id"] = f"call_{generate_id()}"

            messages.append(groq_msg)

        return messages

    def _execute_tool(self, groq_tool_call: object) -> ToolResult:
        """
        Converte um tool_call do Groq em ToolCall interno e executa.
        """
        try:
            params = json.loads(groq_tool_call.function.arguments)
        except (json.JSONDecodeError, AttributeError):
            params = {}

        tool_call = ToolCall(
            tool_name=groq_tool_call.function.name,
            tool_id=groq_tool_call.id,
            parameters=params,
        )
        return self.tool_pool.dispatch(tool_call)

    def _maybe_save_insight(
        self, response_text: str, min_length: int = 200
    ) -> None:
        """
        Detecta se a resposta contém um insight relevante e salva na memória.
        Heurística simples: respostas longas com palavras-chave de análise.
        """
        keywords = [
            "concluí", "identifiquei", "observei", "total de", "média de",
            "maior", "menor", "tendência", "destaque", "importante",
            "recomendo", "sugiro", "atenção", "crítico", "resultado"
        ]
        text_lower = response_text.lower()
        has_keyword = any(kw in text_lower for kw in keywords)

        if has_keyword and len(response_text) >= min_length:
            # Salva o primeiro parágrafo substancial como insight
            first_paragraph = response_text.split("\n\n")[0][:200]
            self.memory.save_insight(
                insight=first_paragraph,
                source_document=self.session.active_document or "",
            )

    # ─── Gestão de documento ativo ───────────────────────────────────────────────

    def load_document(self, filepath: str, filename: str) -> str:
        """
        Carrega um documento na sessão ativa.
        Usa a tool correta baseada na extensão do arquivo.
        Retorna mensagem de confirmação para exibir ao usuário.
        """
        ext = filepath.lower().split(".")[-1]

        tool_name_map = {
            "pdf": "tool_pdf",
            "xlsx": "tool_excel",
            "xls": "tool_excel",
            "csv": "tool_excel",
            "txt": "tool_txt",
            "md": "tool_txt",
        }

        tool_name = tool_name_map.get(ext)
        if not tool_name:
            return f"❌ Formato '.{ext}' não suportado."

        tool_call = ToolCall(
            tool_name=tool_name,
            tool_id=generate_id("load"),
            parameters={"filepath": filepath},
        )
        result = self.tool_pool.dispatch(tool_call)

        if not result.success:
            return f"❌ Erro ao carregar o documento: {result.error}"

        # Salva conteúdo na sessão
        output = result.output
        self.session.active_document = filename
        self.session.document_content = (
            output.get("content", "") if isinstance(output, dict) else str(output)
        )

        # Registra na memória do usuário
        pages = output.get("total_pages", 0) if isinstance(output, dict) else 0
        char_count = output.get("char_count", len(self.session.document_content))
        self.memory.record_document(
            filename=filename,
            summary=f"{char_count:,} caracteres extraídos",
            pages=pages,
        )

        return (
            f"✅ Documento **{filename}** carregado com sucesso! "
            f"({char_count:,} caracteres). "
            f"Pode fazer perguntas sobre ele."
        )
