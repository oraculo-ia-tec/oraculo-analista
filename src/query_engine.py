# ============================================================
# src/query_engine.py
# Camada de comunicação com o LLM (Groq)
# ============================================================
from __future__ import annotations

import streamlit as st
from groq import Groq

from .constants.settings import MAX_TOKENS_FREE_PLAN, DEFAULT_MODEL
from .hooks.cost_hook import CostHook
from .hooks.audit_hook import AuditHook
from .utils.helpers import now_iso


class QueryEngine:
    """
    Envia prompts ao LLM e retorna a resposta.
    Suporta streaming via callback opcional.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS_FREE_PLAN,
        cost_hook: CostHook | None = None,
        audit_hook: AuditHook | None = None,
    ):
        self.client     = Groq(api_key=api_key)
        self.model      = model
        self.max_tokens = max_tokens
        self.cost_hook  = cost_hook
        self.audit_hook = audit_hook

    def query(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[dict] | None = None,
        stream_callback=None,
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        if stream_callback:
            return self._stream(messages, stream_callback)
        return self._complete(messages)

    def _complete(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        text = response.choices[0].message.content or ""
        self._track(response, text)
        return text

    def _stream(self, messages: list[dict], callback) -> str:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            stream=True,
        )
        full = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full += delta
            callback(full)
        return full

    def _track(self, response, text: str) -> None:
        if self.cost_hook:
            usage = getattr(response, "usage", None)
            if usage:
                self.cost_hook.add(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                )
        if self.audit_hook:
            self.audit_hook.log({
                "ts":     now_iso(),
                "model":  self.model,
                "chars":  len(text),
            })
