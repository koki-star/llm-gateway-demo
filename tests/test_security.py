import pytest

from src.gateway import DemoModeError, GatewayError, UnifiedLLMGateway, sample_reply


async def test_blank_prompt_has_safe_error():
    with pytest.raises(GatewayError, match="Enter a prompt"):
        [chunk async for chunk in UnifiedLLMGateway(0).stream("  ", "OpenAI-style / small demo")]


async def test_unknown_model_has_safe_error():
    with pytest.raises(GatewayError, match="Choose one"):
        [chunk async for chunk in UnifiedLLMGateway(0).stream("Hello", "secret model")]


async def test_demo_error_does_not_reveal_dummy_secret():
    dummy_secret = "DUMMY_SECRET_123"
    with pytest.raises(DemoModeError) as caught:
        [chunk async for chunk in UnifiedLLMGateway(0).stream(dummy_secret, "OpenAI-style / small demo", simulate_error=True)]
    assert dummy_secret not in str(caught.value)
    assert "Simulated provider error" in str(caught.value)


def test_sample_reply_does_not_echo_prompt():
    dummy_secret = "DUMMY_SECRET_123"
    assert dummy_secret not in sample_reply(dummy_secret, "OpenAI-style")
