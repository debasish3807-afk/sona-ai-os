"""Ollama local model provider implementation skeleton.

Provides access to locally-hosted models via Ollama (LLaMA, Mistral,
CodeLlama, etc.). Ideal for privacy-focused deployments and offline use.
"""

from collections.abc import AsyncIterator

from providers.base import BaseProvider
from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import OllamaConfig, ProviderConfig
from providers.types import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderID,
    StreamChunk,
)


class OllamaProvider(BaseProvider):
    """Ollama local model provider.

    Supports: Any model available via Ollama (LLaMA 3, Mistral,
              CodeLlama, Phi, Gemma, etc.)
    Capabilities: chat, streaming, embeddings, code generation.
    Note: Runs locally — no API key required, no rate limits.
    """

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self._config = config or OllamaConfig()
        self._initialized = False
        self._capabilities = CapabilitySet(
            provider_id=ProviderID.OLLAMA,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.EMBEDDINGS, CapabilityLevel.INTERMEDIATE),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.INTERMEDIATE),
            ],
        )

    @property
    def provider_id(self) -> ProviderID:
        """See base class."""
        return ProviderID.OLLAMA

    @property
    def display_name(self) -> str:
        """See base class."""
        return "Ollama (Local)"

    @property
    def config(self) -> ProviderConfig:
        """See base class."""
        return self._config

    @property
    def capabilities(self) -> CapabilitySet:
        """See base class."""
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        """See base class."""
        return self._initialized

    async def initialize(self) -> None:
        # TODO: Verify Ollama server is reachable at base_url
        """See base class."""
        self._initialized = True

    async def shutdown(self) -> None:
        """See base class."""
        self._initialized = False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # TODO: Implement Ollama /api/chat endpoint
        """See base class."""
        raise NotImplementedError("Ollama chat not yet implemented")

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        # TODO: Implement Ollama streaming chat
        """See base class."""
        raise NotImplementedError("Ollama stream not yet implemented")
        yield  # type: ignore[misc]

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        # TODO: Implement Ollama /api/embeddings endpoint
        """See base class."""
        raise NotImplementedError("Ollama embeddings not yet implemented")

    async def list_models(self) -> list[ModelInfo]:
        # TODO: Query Ollama /api/tags for local models
        """See base class."""
        return []

    async def get_model(self, model_id: str) -> ModelInfo | None:
        """See base class."""
        return None

    def supports_tools(self) -> bool:
        """See base class."""
        return False

    def supports_vision(self) -> bool:
        """See base class."""
        return False

    def supports_function_calling(self) -> bool:
        """See base class."""
        return False

    def supports_streaming(self) -> bool:
        """See base class."""
        return True

    async def health(self) -> bool:
        # TODO: Check Ollama server connectivity
        """See base class."""
        return self._initialized
