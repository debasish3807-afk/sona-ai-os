"""Request/response schemas for the AI Brain and Chat API.

Pydantic models for the public API surface. These are separate from
the internal provider types to allow independent evolution.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    """A single message in a chat conversation."""

    role: str = Field(..., description="Message role: system, user, assistant, tool")
    content: str = Field(..., description="Message content")
    name: str | None = Field(default=None, description="Optional sender name")


class ChatEndpointRequest(BaseModel):
    """POST /api/v1/chat request body."""

    messages: list[ChatMessageSchema] = Field(..., min_length=1)
    model: str | None = Field(default=None, description="Target model (auto-select if omitted)")
    provider: str | None = Field(
        default=None, description="Target provider (auto-select if omitted)"
    )
    session_id: str | None = Field(default=None, description="Session ID for memory context")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    stream: bool = Field(default=False, description="Enable SSE streaming")
    system_prompt: str | None = Field(default=None, description="Override system prompt")


class TokenUsageSchema(BaseModel):
    """Token consumption statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatEndpointResponse(BaseModel):
    """POST /api/v1/chat response body."""

    success: bool = True
    response_id: str
    content: str
    model: str
    provider: str
    agent: str | None = None
    finish_reason: str = "stop"
    token_usage: TokenUsageSchema
    latency_ms: float
    session_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ModelInfoSchema(BaseModel):
    """Public model information."""

    model_id: str
    name: str
    provider: str
    model_type: str = "chat"
    max_context_tokens: int = 8192
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False


class ModelListResponse(BaseModel):
    """GET /api/v1/models response."""

    success: bool = True
    models: list[ModelInfoSchema]
    total: int


class ProviderInfoSchema(BaseModel):
    """Provider summary info."""

    provider_id: str
    name: str
    enabled: bool
    healthy: bool
    models_count: int


class ProviderListResponse(BaseModel):
    """GET /api/v1/providers response."""

    success: bool = True
    providers: list[ProviderInfoSchema]


class ProviderHealthDetail(BaseModel):
    """Health detail for a single provider."""

    provider_id: str
    name: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None


class ProviderHealthResponse(BaseModel):
    """GET /api/v1/health/providers response."""

    success: bool = True
    providers: list[ProviderHealthDetail]


# Internal types used by the Brain orchestrator


class BrainRequest(BaseModel):
    """Internal request flowing through the Brain pipeline."""

    messages: list[ChatMessageSchema]
    model: str | None = None
    provider: str | None = None
    session_id: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrainResponse(BaseModel):
    """Internal response from the Brain pipeline."""

    content: str
    model: str
    provider: str
    agent: str | None = None
    finish_reason: str = "stop"
    token_usage: TokenUsageSchema = Field(default_factory=TokenUsageSchema)
    latency_ms: float = 0.0
    response_id: str = ""
    session_id: str | None = None


class BrainStreamChunk(BaseModel):
    """A single SSE chunk from the Brain streaming pipeline."""

    event: str
    content: str = ""
    model: str = ""
    finish_reason: str | None = None
    token_usage: TokenUsageSchema | None = None
