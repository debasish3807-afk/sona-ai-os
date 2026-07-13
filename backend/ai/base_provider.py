"""Abstract base class for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ai.schemas import AIRequest, AIResponse, ProviderConfig, ProviderStatus
from config.logging import get_logger

logger = get_logger(__name__)


class BaseAIProvider(ABC):
    """Abstract base for all AI provider implementations."""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._status = ProviderStatus.UNKNOWN
        self._request_count = 0
        self._error_count = 0

    @abstractmethod
    async def complete(self, request: AIRequest) -> AIResponse:
        """Generate a completion for the given request."""

    @abstractmethod
    def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream completion chunks for the given request."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and reachable."""

    def get_status(self) -> ProviderStatus:
        """Return current provider status."""
        return self._status

    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        return False

    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        return False

    def supports_vision(self) -> bool:
        """Whether this provider supports vision/image inputs."""
        return False

    @property
    def name(self) -> str:
        """Provider name from config."""
        return self._config.name

    @property
    def available_models(self) -> list[str]:
        """List of models available from this provider."""
        return self._config.models
