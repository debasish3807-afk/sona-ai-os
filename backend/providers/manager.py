"""Provider orchestration manager.

Coordinates provider selection, fallback chains, health monitoring,
and request routing. Acts as the primary interface between the AI
kernel and the provider system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from providers.base import BaseProvider
from providers.capabilities import Capability, CapabilityRequirement
from providers.config import ProviderConfig
from providers.factory import ProviderFactory
from providers.health import HealthMonitor, ProviderHealthStatus
from providers.registry import ProviderRegistry
from providers.types import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderID,
    StreamChunk,
)



class SelectionStrategy(str):
    """Provider selection strategies."""

    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    COST_OPTIMIZED = "cost_optimized"
    CAPABILITY_MATCH = "capability_match"


@dataclass
class ProviderManagerConfig:
    """Configuration for the provider manager.

    Attributes:
        default_strategy: Default provider selection strategy.
        enable_fallback: Whether to attempt fallback providers.
        max_fallback_attempts: Maximum fallback attempts.
        health_check_interval_seconds: Interval for periodic health checks.
        auto_discover: Whether to auto-discover configured providers.
        fallback_order: Explicit fallback provider order.
        metadata: Additional configuration.
    """

    default_strategy: str = SelectionStrategy.PRIORITY
    enable_fallback: bool = True
    max_fallback_attempts: int = 3
    health_check_interval_seconds: int = 30
    auto_discover: bool = True
    fallback_order: List[ProviderID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)



class ProviderManager(ABC):
    """Abstract interface for provider orchestration.

    The ProviderManager is the primary interface between the kernel
    and AI providers. It handles:
    - Provider selection based on requirements
    - Automatic fallback on failure
    - Health monitoring and circuit breaking
    - Request routing and load distribution
    """

    @property
    @abstractmethod
    def registry(self) -> ProviderRegistry:
        """Access the provider registry."""
        ...

    @property
    @abstractmethod
    def health_monitor(self) -> HealthMonitor:
        """Access the health monitor."""
        ...

    @property
    @abstractmethod
    def factory(self) -> ProviderFactory:
        """Access the provider factory."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def initialize(
        self, config: Optional[ProviderManagerConfig] = None
    ) -> None:
        """Initialize the provider manager.

        Discovers available providers, registers them, and starts
        health monitoring.

        Args:
            config: Optional configuration override.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider manager and all providers."""
        ...

    # ------------------------------------------------------------------
    # Core Operations (with automatic selection + fallback)
    # ------------------------------------------------------------------

    @abstractmethod
    async def chat(
        self,
        request: ChatRequest,
        provider_id: Optional[ProviderID] = None,
        requirements: Optional[CapabilityRequirement] = None,
    ) -> ChatResponse:
        """Execute a chat completion with automatic provider selection.

        Selects the best provider, executes the request, and falls
        back to alternatives on failure.

        Args:
            request: Chat request payload.
            provider_id: Optional explicit provider selection.
            requirements: Optional capability requirements.

        Returns:
            ChatResponse from the selected provider.

        Raises:
            AllProvidersFailed: If all providers fail.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        request: ChatRequest,
        provider_id: Optional[ProviderID] = None,
        requirements: Optional[CapabilityRequirement] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat with automatic provider selection.

        Args:
            request: Chat request payload.
            provider_id: Optional explicit provider selection.
            requirements: Optional capability requirements.

        Yields:
            StreamChunk instances as content is generated.

        Raises:
            AllProvidersFailed: If all providers fail.
        """
        ...

    @abstractmethod
    async def embeddings(
        self,
        request: EmbeddingRequest,
        provider_id: Optional[ProviderID] = None,
    ) -> EmbeddingResponse:
        """Generate embeddings with automatic provider selection.

        Args:
            request: Embedding request payload.
            provider_id: Optional explicit provider selection.

        Returns:
            EmbeddingResponse with vectors.

        Raises:
            AllProvidersFailed: If all providers fail.
        """
        ...


    # ------------------------------------------------------------------
    # Provider Selection
    # ------------------------------------------------------------------

    @abstractmethod
    async def select_provider(
        self,
        requirements: Optional[CapabilityRequirement] = None,
        strategy: Optional[str] = None,
    ) -> Optional[BaseProvider]:
        """Select the best provider for given requirements.

        Args:
            requirements: Capability requirements to match.
            strategy: Selection strategy override.

        Returns:
            Selected provider or None if no match.
        """
        ...

    @abstractmethod
    async def get_fallback_chain(
        self,
        primary: ProviderID,
        requirements: Optional[CapabilityRequirement] = None,
    ) -> List[BaseProvider]:
        """Get the fallback chain for a primary provider.

        Args:
            primary: The primary provider to build chain for.
            requirements: Optional capability filter.

        Returns:
            Ordered list of fallback providers.
        """
        ...

    # ------------------------------------------------------------------
    # Discovery & Information
    # ------------------------------------------------------------------

    @abstractmethod
    async def list_models(
        self, provider_id: Optional[ProviderID] = None
    ) -> List[ModelInfo]:
        """List available models across all or specific providers.

        Args:
            provider_id: Optional filter by provider.

        Returns:
            List of ModelInfo from available providers.
        """
        ...

    @abstractmethod
    async def get_health_status(self) -> Dict[ProviderID, ProviderHealthStatus]:
        """Get health status for all registered providers.

        Returns:
            Mapping of provider IDs to their health statuses.
        """
        ...

    @abstractmethod
    async def get_available_providers(self) -> List[ProviderID]:
        """Get list of currently available provider IDs.

        Returns:
            List of available provider identifiers.
        """
        ...

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    @abstractmethod
    async def add_provider(
        self,
        provider_id: ProviderID,
        config: Optional[ProviderConfig] = None,
        priority: int = 50,
    ) -> bool:
        """Add and register a new provider.

        Args:
            provider_id: The provider to add.
            config: Optional configuration override.
            priority: Selection priority.

        Returns:
            True if successfully added.
        """
        ...

    @abstractmethod
    async def remove_provider(self, provider_id: ProviderID) -> bool:
        """Remove a provider from the system.

        Args:
            provider_id: The provider to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    async def set_priority(
        self, provider_id: ProviderID, priority: int
    ) -> None:
        """Update a provider's selection priority.

        Args:
            provider_id: The provider to update.
            priority: New priority value (lower = preferred).
        """
        ...

    @abstractmethod
    async def set_fallback_order(self, order: List[ProviderID]) -> None:
        """Set the explicit fallback order for providers.

        Args:
            order: Ordered list of provider IDs for fallback.
        """
        ...
