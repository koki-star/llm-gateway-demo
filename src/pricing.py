"""Illustrative rates for a classroom simulation. These are not official prices."""

from decimal import Decimal, ROUND_HALF_UP


# USD per one million tokens. These fixed example rates make offline tests repeatable.
DEMO_RATES = {
    "OpenAI-style / small demo": (Decimal("0.20"), Decimal("0.80")),
    "OpenAI-style / large demo": (Decimal("1.50"), Decimal("6.00")),
    "Anthropic-style / small demo": (Decimal("0.25"), Decimal("1.25")),
    "Anthropic-style / large demo": (Decimal("2.00"), Decimal("10.00")),
}


def hypothetical_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """Return an illustrative cost, rounded to six decimal places."""
    input_rate, output_rate = DEMO_RATES[model]
    amount = (Decimal(prompt_tokens) * input_rate + Decimal(completion_tokens) * output_rate) / Decimal(1_000_000)
    return amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
