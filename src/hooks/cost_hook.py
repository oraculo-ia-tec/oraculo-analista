# ============================================================
# src/hooks/cost_hook.py
# Hook de custo — intercepta toda chamada ao LLM e acumula
# o gasto estimado da sessão (estilo Claude Code costHook)
# ============================================================
from ..utils.helpers import estimate_tokens
from ..constants.settings import COST_PER_1M_INPUT_TOKENS, COST_PER_1M_OUTPUT_TOKENS


class CostHook:
    """
    Rastreia tokens consumidos e custo acumulado na sessão.

    Uso:
        hook = CostHook()
        hook.on_request(system_prompt + user_prompt)
        hook.on_response(assistant_text)
        print(hook.summary())
    """

    def __init__(self):
        self.input_tokens  = 0
        self.output_tokens = 0
        self._calls        = 0

    def on_request(self, prompt_text: str) -> None:
        """Chamado antes de enviar ao LLM."""
        self.input_tokens += estimate_tokens(prompt_text)
        self._calls += 1

    def on_response(self, response_text: str) -> None:
        """Chamado após receber a resposta do LLM."""
        self.output_tokens += estimate_tokens(response_text)

    @property
    def cost_usd(self) -> float:
        """Custo estimado em USD."""
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
