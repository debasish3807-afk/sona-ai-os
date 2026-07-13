"""Data schemas for the unified AI layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


@dataclass
class AIMessage:
    """A single message in a conversation."""

    role: str
    content: str
    name: str = ""


@dataclass
class AIRequest:
    """Request payload for AI completion."""

    messages: list[AIMessage]
    model: str = ""
    provider: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    tools: list[dict] | None = None
    system_prompt: str = ""


@dataclass
class AIResponse:
    """Response from an AI provider."""

    content: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    tool_calls: list[dict] = field(default_factory=list)
    response_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class TokenUsage:
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""

    name: str
    api_key: str = ""
    base_url: str = ""
    models: list[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: float = 60.0
    enabled: bool = True


class ProviderStatus(str, Enum):
    """Health status of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
