"""Types shared by the two simulated provider adapters and the UI."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


Provider = Literal["OpenAI-style", "Anthropic-style"]


class ChunkTelemetry(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_seconds: float = Field(ge=0)
    ttft_ms: float = Field(ge=0)
    tokens_per_second: float = Field(ge=0)
    hypothetical_cost_usd: Decimal = Field(ge=0)
    usage_source: str = "Local word-count estimate, not provider usage"


class StreamChunk(BaseModel):
    delta_text: str
    provider: Provider
    model: str
    is_final: bool = False
    telemetry: ChunkTelemetry | None = None
