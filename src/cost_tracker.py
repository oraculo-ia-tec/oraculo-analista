"""
Cost Tracker — rastreia consumo de tokens e custo estimado em USD.
Atualizações de preço: editar PRICE_PER_1M_TOKENS.
"""
from dataclasses import dataclass, field
from datetime import datetime

# Preços Groq (junho 2025) — por 1M tokens
PRICE_PER_1M_TOKENS = {
    "llama-3.3-70b-versatile":       {"input": 0.59, "output": 0.79},
    "llama3-70b-8192":               {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant":          {"input": 0.05, "output": 0.08},
    "gemma2-9b-it":                  {"input": 0.20, "output": 0.20},
    "default":                       {"input": 0.59, "output": 0.79},
}


@dataclass
class TokenUsage:
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        prices = PRICE_PER_1M_TOKENS.get(self.model, PRICE_PER_1M_TOKENS["default"])
        return (
            self.input_tokens * prices["input"] / 1_000_000
            + self.output_tokens * prices["output"] / 1_000_000
        )


class CostTracker:
    """
    Rastreia custo acumulado de uma sessão.
    Usado pelo app.py para exibir o custo em tempo real na sidebar.
    """

    def __init__(self):
        self._usages: list[TokenUsage] = []

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        self._usages.append(TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ))

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self._usages)

    @property
    def total_cost_usd(self) -> float:
        return sum(u.cost_usd for u in self._usages)

    @property
    def total_cost_brl(self) -> float:
        """Conversão aproximada USD → BRL (taxa fixa para simplicidade)."""
        return self.total_cost_usd * 5.10

    def summary(self) -> dict:
        return {
            "total_calls": len(self._usages),
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
            "cost_brl": round(self.total_cost_brl, 4),
        }

    def reset(self) -> None:
        self._usages.clear()
