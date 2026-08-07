"""Data models for the LLM Client library.

Defines provider configuration, message, and response models used
across all LLM provider interactions.
"""

from dataclasses import dataclass
from enum import StrEnum


class ProviderType(StrEnum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration for an LLM provider connection.

    Attributes:
        provider: The LLM provider type.
        api_key: Authentication key for the provider (optional for local providers like Ollama).
        base_url: Base URL for the provider API endpoint.
        model_id: Identifier of the model to use.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature for generation.
        timeout_seconds: Request timeout in seconds.
    """

    provider: ProviderType
    model_id: str
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 60


@dataclass(frozen=True)
class Message:
    """A single message in a conversation.

    Attributes:
        role: The role of the message sender (e.g., "user", "assistant", "system").
        content: The text content of the message.
    """

    role: str
    content: str


@dataclass(frozen=True)
class CompletionResult:
    """Result from an LLM completion request.

    Attributes:
        content: The generated text content.
        model: The model identifier that produced the response.
        tokens_input: Number of input/prompt tokens consumed.
        tokens_output: Number of output/completion tokens generated.
        latency_ms: Total request latency in milliseconds.
    """

    content: str
    model: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
