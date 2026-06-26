# ============================================================
# src/query_engine.py
# Motor de consultas ao LLM — coração do loop agêntico
# ============================================================
from __future__ import annotations

import time

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
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS_FREE_PLAN,
        cost_hook: CostHook | None = None,
        audit_hook: AuditHook | None = None,
    ):
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY não encontrada. "
                "Configure-a nos Secrets do Streamlit Cloud "
                "(Settings → Secrets → GROQ_API_KEY)."
            )
        self._client    = Groq(api_key=api_key)
        self.model      = model
        self.max_tokens = max_tokens
        self.cost_hook  = cost_hook  or CostHook()
        self.audit_hook = audit_hook or AuditHook()

    def query(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[dict] | None = None,
        stream_callback=None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        messages = self._build_messages(system_prompt, user_prompt, history)
        full_prompt_text = " ".join(m["content"] for m in messages)

        self.cost_hook.on_request(full_prompt_text)
        self.audit_hook.on_llm_call(self.model, len(full_prompt_text))

        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                full_response = ""
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

                clean_response = strip_think_tags(full_response)
                self.cost_hook.on_response(clean_response)
                return clean_response

            except Exception as exc:
                last_exc = exc
                self.audit_hook.on_error("QueryEngine", f"tentativa {attempt}: {exc}")
                if attempt < max_retries:
                    time.sleep(retry_delay * attempt)

        raise last_exc

    def _build_messages(self, system_prompt, user_prompt, history):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in (history or [])[-MAX_HISTORY_MESSAGES:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})
        return messages
