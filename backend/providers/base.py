"""Abstract provider interface.

Defines the contract that all AI provider implementations must
fulfill. This is the core abstraction enabling provider-agnostic
AI operations throughout Sona AI OS.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from providers.capabilities import CapabilitySet
from providers.config import ProviderConfig
from providers.types import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderID,
    StreamChunk,
)


class BaseProvider(ABC):
    """Abstract base class for all AI providers.

    Every provider (OpenAI, Claude, Gemini, etc.) must implement
    this interface to participate in the provider system.
    """

    @property
    @abstractmethod
    def provider_id(self) -> ProviderID:
        """Unique identifier for this provider."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> CapabilitySet:
        """Declared capabilities of this provider."""
        ...

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether the provider has been initialized."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Load API keys from environment, validate configuration,
        and establish any required connections.

        Raises:
            ProviderAuthenticationError: If API key is missing/invalid.
            ProviderConnectionError: If initial connection fails.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider gracefully.

        Close connections and release resources. Must be idempotent.
        """
        ...

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute a chat completion request.

        Args:
            request: The chat request payload.

        Returns:
            ChatResponse with generated content.

        Raises:
            ProviderError: On any provider-level failure.
            ModelNotFoundError: If the requested model is unavailable.
            ProviderRateLimitError: If rate limits are exceeded.
        """
        ...

    @abstractmethod
    def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat completion request.

        Args:
            request: The chat request payload (stream=True implied).

        Yields:
            StreamChunk instances as content is generated.

        Raises:
            ProviderError: On any provider-level failure.
        """
        ...

    @abstractmethod
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate text embeddings.

        Args:
            request: The embedding request payload.

        Returns:
            EmbeddingResponse with embedding vectors.

        Raises:
            ProviderError: On any provider-level failure.
        """
        ...

    # ------------------------------------------------------------------
    # Discovery & Capabilities
    # ------------------------------------------------------------------

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List all models available from this provider.

        Returns:
            List of ModelInfo for available models.
        """
        ...

    @abstractmethod
    async def get_model(self, model_id: str) -> ModelInfo | None:
        """Get information about a specific model.

        Args:
            model_id: The model identifier.

        Returns:
            ModelInfo or None if not available.
        """
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this provider supports tool/function calling.

        Returns:
            True if tool calling is supported.
        """
        ...

    @abstractmethod
    def supports_vision(self) -> bool:
        """Check if this provider supports vision/image inputs.

        Returns:
            True if vision is supported.
        """
        ...

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Check if this provider supports function calling.

        Returns:
            True if function calling is supported.
        """
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming responses.

        Returns:
            True if streaming is supported.
        """
        ...

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @abstractmethod
    async def health(self) -> bool:
        """Perform a lightweight health check.

        Returns:
            True if the provider is healthy and reachable.
        """
        ...
