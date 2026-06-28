# ============================================================
# src/hooks/cost_hook.py
# Hook de custo — rastreia tokens e custo estimado por sessão
# ============================================================
from __future__ import annotations

from ..constants.settings import COST_PER_1M_INPUT_TOKENS, COST_PER_1M_OUTPUT_TOKENS


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class CostHook:
    """
    Rastreia tokens consumidos e custo acumulado na sessão.
    """

    def __init__(self):
        self.input_tokens  = 0
        self.output_tokens = 0
        self._calls        = 0

    def on_request(self, prompt_text: str) -> None:
        self.input_tokens += _estimate_tokens(prompt_text)
        self._calls += 1

    def on_response(self, response_text: str) -> None:
        self.output_tokens += _estimate_tokens(response_text)

    def add(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Adiciona tokens direto da resposta do LLM."""
        self.input_tokens  += prompt_tokens
        self.output_tokens += completion_tokens
        self._calls        += 1

    @property
    def cost_usd(self) -> float:
        input_cost  = (self.input_tokens  / 1_000_000) * COST_PER_1M_INPUT_TOKENS
        output_cost = (self.output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

    def summary(self) -> dict:
        return {
            "calls":         self._calls,
            "input_tokens":  self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens":  self.input_tokens + self.output_tokens,
            "cost_usd":      self.cost_usd,
        }

    def reset(self) -> None:
        self.input_tokens  = 0
        self.output_tokens = 0
        self._calls        = 0
