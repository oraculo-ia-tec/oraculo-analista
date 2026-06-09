# ============================================================
# src/query_engine.py
# Motor de consultas ao LLM — coração do loop agêntico
# Equivalente ao QueryEngine do Claude Code
# ============================================================
from __future__ import annotations

from groq import Groq

from .constants.settings import (
    DEFAULT_MODEL,
    MAX_HISTORY_MESSAGES,
    MAX_TOKENS_FREE_PLAN,
)
from .hooks.cost_hook import CostHook
from .hooks.audit_hook import AuditHook
from .utils.helpers import truncate, strip_think_tags, estimate_tokens


class QueryEngine:
    """
    Responsável por:
      1. Montar o payload de mensagens (system + history + user)
      2. Chamar o LLM via streaming
      3. Notificar hooks de custo e auditoria
      4. Retornar o texto limpo gerado

    Parâmetros:
        api_key      → chave Groq
        model        → modelo LLM (padrão: DEFAULT_MODEL)
        max_tokens   → limite de tokens na resposta
        cost_hook    → instância de CostHook (opcional)
        audit_hook   → instância de AuditHook (opcional)
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS_FREE_PLAN,
        cost_hook: CostHook | None = None,
        audit_hook: AuditHook | None = None,
    ):
        self._client    = Groq(api_key=api_key)
        self.model      = model
        self.max_tokens = max_tokens
        self.cost_hook  = cost_hook  or CostHook()
        self.audit_hook = audit_hook or AuditHook()

    # ── API pública ──────────────────────────────────────────

    def query(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[dict] | None = None,
        stream_callback=None,
    ) -> str:
        """
        Executa uma consulta ao LLM.

        Args:
            system_prompt   → contexto e instruções do agente
            user_prompt     → mensagem atual do usuário
            history         → lista de {role, content} anteriores
            stream_callback → callable(delta: str) chamado a cada chunk

        Returns:
            Texto final limpo (sem tags <think>).
        """
        messages = self._build_messages(system_prompt, user_prompt, history)
        full_prompt_text = " ".join(m["content"] for m in messages)

        # ── hooks de pré-chamada ──────────────────────────────
        self.cost_hook.on_request(full_prompt_text)
        self.audit_hook.on_llm_call(self.model, len(full_prompt_text))

        # ── chamada ao LLM ────────────────────────────────────
        full_response = ""
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=self.max_tokens,
                top_p=1,
                stream=True,
            )
            for event in stream:
                if event.choices:
                    delta = event.choices[0].delta.content or ""
                    full_response += delta
                    if stream_callback:
                        clean = strip_think_tags(full_response)
                        stream_callback(clean)

        except Exception as exc:  # noqa: BLE001
            self.audit_hook.on_error("QueryEngine", str(exc))
            raise

        clean_response = strip_think_tags(full_response)

        # ── hooks de pós-chamada ──────────────────────────────
        self.cost_hook.on_response(clean_response)

        return clean_response

    # ── internals ────────────────────────────────────────────

    def _build_messages(self, system_prompt, user_prompt, history):
        messages = [{"role": "system", "content": system_prompt}]

        for msg in (history or [])[-MAX_HISTORY_MESSAGES:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_prompt})
        return messages
