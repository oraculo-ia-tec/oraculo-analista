# ============================================================
# src/hooks/cost_hook.py
# Hook de custo — rastreia tokens e custo estimado por sessão
# ============================================================
from __future__ import annotations

# Custo aproximado por token (USD) — modelo llama-3.3-70b via Groq
_COST_PER_TOKEN = 0.0000008


class CostHook:
    def __init__(self):
        self._input_tokens  = 0
        self._output_tokens = 0
        self._calls         = 0

    def on_request(self, prompt_text: str) -> None:
        tokens = max(1, len(prompt_text) // 4)
        self._input_tokens += tokens
        self._calls        += 1

    def on_response(self, response_text: str) -> None:
        tokens = max(1, len(response_text) // 4)
        self._output_tokens += tokens

    def summary(self) -> dict:
        total = self._input_tokens + self._output_tokens
        return {
            "input_tokens":  self._input_tokens,
            "output_tokens": self._output_tokens,
            "total_tokens":  total,
            "calls":         self._calls,
            "cost_usd":      total * _COST_PER_TOKEN,
        }

    def reset(self) -> None:
        self._input_tokens  = 0
        self._output_tokens = 0
        self._calls         = 0
