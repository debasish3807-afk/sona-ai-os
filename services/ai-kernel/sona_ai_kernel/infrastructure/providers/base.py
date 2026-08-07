"""Base provider interface for LLM backends.

Defines the abstract contract that all LLM provider adapters must
implement, along with shared data structures for completions and health.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ProviderHealth:
    """Health status of an LLM provider.

    Attributes:
        healthy: Whether the provider is currently responsive.
        last_check: Timestamp of the most recent health check.
        error: Error message from the last failed health check, if any.
        latency_ms: Latency of the last health check in milliseconds.
    """

    healthy: bool = True
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None
    latency_ms: float = 0.0


@dataclass(frozen=True)
class CompletionRequest:
    """Request payload for an LLM completion.

    Attributes:
        messages: Conversation messages in OpenAI-style format.
        model: Model identifier to use for completion.
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum tokens to generate.
        top_p: Nucleus sampling parameter.
        stream: Whether to stream the response.
    """

    messages: list[dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stream: bool = False


@dataclass(frozen=True)
class CompletionResponse:
    """Response payload from an LLM completion.

    Attributes:
        content: Generated text content.
        model: The model that produced the response.
        tokens_input: Number of input/prompt tokens consumed.
        tokens_output: Number of output/completion tokens generated.
        finish_reason: Reason the model stopped generating.
    """

    content: str
    model: str
    tokens_input: int
    tokens_output: int
    finish_reason: str = "stop"


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for an LLM provider connection.

    Attributes:
        name: Unique provider identifier (e.g., "ollama", "openai").
        base_url: Base URL for the provider's API.
        api_key: Optional API key for authentication.
        timeout_seconds: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        models: List of pre-configured model identifiers.
    """

    name: str
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 60.0
    max_retries: int = 3
    models: list[str] = field(default_factory=list)


class LLMProviderBase(ABC):
    """Abstract base for all LLM provider adapters.

    Concrete implementations connect to specific LLM backends
    (Ollama, OpenAI, Anthropic, etc.) and translate between the
    internal CompletionRequest/Response format and provider APIs.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider with its configuration.

        Args:
            config: Provider connection configuration.
        """
        self.config = config
        self._health = ProviderHealth()

    @property
    def name(self) -> str:
        """Return the provider's unique name."""
        return self.config.name

    @property
    def health(self) -> ProviderHealth:
        """Return the current health status."""
        return self._health

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a non-streaming completion.

        Args:
            request: The completion request payload.

        Returns:
            A CompletionResponse with generated content and usage metrics.
        """
        ...

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens.

        Args:
            request: The completion request payload (stream flag is ignored).

        Yields:
            String tokens/chunks as they are generated.
        """
        ...

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Check provider availability and responsiveness.

        Returns:
            Updated ProviderHealth with current status.
        """
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models from this provider.

        Returns:
            A list of model identifier strings.
        """
        ...

    async def close(self) -> None:
        """Close any open connections. Override in subclasses if needed."""
