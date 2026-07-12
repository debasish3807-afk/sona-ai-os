"""Ollama local model provider implementation skeleton.

Provides access to locally-hosted models via Ollama (LLaMA, Mistral,
CodeLlama, etc.). Ideal for privacy-focused deployments and offline use.
"""

from typing import AsyncIterator, List, Optional

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

    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
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
        return ProviderID.OLLAMA

    @property
    def display_name(self) -> str:
        return "Ollama (Local)"

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        # TODO: Verify Ollama server is reachable at base_url
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # TODO: Implement Ollama /api/chat endpoint
        raise NotImplementedError("Ollama chat not yet implemented")

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        # TODO: Implement Ollama streaming chat
        raise NotImplementedError("Ollama stream not yet implemented")
        yield  # type: ignore[misc]

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        # TODO: Implement Ollama /api/embeddings endpoint
        raise NotImplementedError("Ollama embeddings not yet implemented")

    async def list_models(self) -> List[ModelInfo]:
        # TODO: Query Ollama /api/tags for local models
        return []

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        return None

    def supports_tools(self) -> bool:
        return False

    def supports_vision(self) -> bool:
        return False

    def supports_function_calling(self) -> bool:
        return False

    def supports_streaming(self) -> bool:
        return True

    async def health(self) -> bool:
        # TODO: Check Ollama server connectivity
        return self._initialized
