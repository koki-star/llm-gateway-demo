"""Two local event formats normalized into one async stream. No network calls."""

import asyncio
import re
from collections.abc import AsyncGenerator
from time import perf_counter

from .pricing import DEMO_RATES, hypothetical_cost
from .schemas import ChunkTelemetry, Provider, StreamChunk


class GatewayError(Exception):
    """Safe error shown to the user without exposing internal details."""


class DemoModeError(GatewayError):
    """Used to demonstrate a recoverable provider failure."""


def estimated_tokens(text: str) -> int:
    """Count word and punctuation groups. This is not a model tokenizer."""
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def sample_reply(prompt: str, provider: Provider) -> str:
    """A local sample reply that is clearly recognizable as a simulation."""
    # Do not repeat the user's prompt in the displayed sample response.
    topic = "async streaming" if "async" in prompt.lower() else "your question"
    if provider == "OpenAI-style":
        return f"Simulated OpenAI-style reply about {topic}. Start with one clear goal, then test a small example."
    return f"Simulated Anthropic-style reply about {topic}. Break the task into small steps and check the result."


class UnifiedLLMGateway:
    """Presents two simulated providers through one streaming interface."""

    def __init__(self, delay_seconds: float = 0.06):
        self.delay_seconds = delay_seconds

    async def _openai_style_events(self, reply: str) -> AsyncGenerator[dict, None]:
        for word in reply.split():
            await asyncio.sleep(self.delay_seconds)
            yield {"choices": [{"delta": {"content": word + " "}}]}
        yield {"choices": [], "usage": {"completion_tokens": estimated_tokens(reply)}}

    async def _anthropic_style_events(self, reply: str) -> AsyncGenerator[dict, None]:
        yield {"type": "message_start"}
        for word in reply.split():
            await asyncio.sleep(self.delay_seconds)
            yield {"type": "content_block_delta", "delta": {"text": word + " "}}
        yield {"type": "message_delta", "usage": {"output_tokens": estimated_tokens(reply)}}

    async def stream(
        self, prompt: str, model: str, temperature: float = 0.7,
        simulate_error: bool = False,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Yield local sample text and telemetry in the same shape for both adapters."""
        if not prompt.strip():
            raise GatewayError("Enter a prompt first.")
        if model not in DEMO_RATES:
            raise GatewayError("Choose one of the demo models.")
        if not 0 <= temperature <= 1:
            raise GatewayError("Temperature must be between 0 and 1.")
        if simulate_error:
            raise DemoModeError("Simulated provider error. The app is still running.")

        provider: Provider = "OpenAI-style" if model.startswith("OpenAI-style") else "Anthropic-style"
        reply = sample_reply(prompt, provider)
        prompt_count = estimated_tokens(prompt)
        started = perf_counter()
        first_text_at: float | None = None
        text_so_far = ""
        events = self._openai_style_events(reply) if provider == "OpenAI-style" else self._anthropic_style_events(reply)

        async for event in events:
            if provider == "OpenAI-style":
                choices = event.get("choices") or []
                delta = (choices[0].get("delta", {}).get("content") or "") if choices else ""
            else:
                delta = event.get("delta", {}).get("text", "") if event.get("type") == "content_block_delta" else ""
            if not delta:
                continue
            now = perf_counter()
            if first_text_at is None:
                first_text_at = now
            text_so_far += delta
            output_count = estimated_tokens(text_so_far)
            elapsed = max(now - started, 0.000001)
            # Include the wait for the first text so the first update does not
            # display an artificial million-token-per-second spike.
            generation_time = elapsed
            metrics = ChunkTelemetry(
                prompt_tokens=prompt_count,
                completion_tokens=output_count,
                latency_seconds=elapsed,
                ttft_ms=(first_text_at - started) * 1000,
                tokens_per_second=output_count / generation_time,
                hypothetical_cost_usd=hypothetical_cost(model, prompt_count, output_count),
            )
            yield StreamChunk(delta_text=delta, provider=provider, model=model, telemetry=metrics)

        ended = perf_counter()
        total_output = estimated_tokens(text_so_far)
        generation_time = max(ended - started, 0.000001)
        final_metrics = ChunkTelemetry(
            prompt_tokens=prompt_count,
            completion_tokens=total_output,
            latency_seconds=ended - started,
            ttft_ms=((first_text_at or ended) - started) * 1000,
            tokens_per_second=total_output / generation_time,
            hypothetical_cost_usd=hypothetical_cost(model, prompt_count, total_output),
        )
        yield StreamChunk(delta_text="", provider=provider, model=model, is_final=True, telemetry=final_metrics)
