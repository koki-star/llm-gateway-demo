import pytest

from src.gateway import UnifiedLLMGateway, estimated_tokens
from src.pricing import hypothetical_cost
from src.schemas import StreamChunk


@pytest.mark.parametrize("model", ["OpenAI-style / small demo", "Anthropic-style / small demo"])
async def test_both_adapters_yield_normalized_stream(model):
    chunks = [chunk async for chunk in UnifiedLLMGateway(0).stream("Explain a loop.", model)]
    assert all(isinstance(chunk, StreamChunk) for chunk in chunks)
    assert len(chunks) > 2
    assert chunks[-1].is_final
    assert "Simulated" in "".join(chunk.delta_text for chunk in chunks)


async def test_final_telemetry_is_positive_and_locally_estimated():
    prompt = "one two three four five"
    chunks = [chunk async for chunk in UnifiedLLMGateway(0).stream(prompt, "OpenAI-style / large demo")]
    telemetry = chunks[-1].telemetry
    assert telemetry.prompt_tokens == estimated_tokens(prompt)
    assert telemetry.completion_tokens > 0
    assert telemetry.ttft_ms > 0
    assert telemetry.tokens_per_second > 0
    assert telemetry.hypothetical_cost_usd > 0
    assert "not provider usage" in telemetry.usage_source


def test_example_cost_has_six_decimal_places():
    cost = hypothetical_cost("OpenAI-style / large demo", 20, 30)
    assert str(cost) == "0.000210"
