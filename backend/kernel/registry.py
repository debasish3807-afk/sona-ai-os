"""Provider registry for AI kernel.

Manages registration, discovery, and lifecycle of AI providers
(LLM services, embedding providers, tool providers, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ProviderType(str, Enum):
    """Classification of provider types."""

    LLM = "llm"
    EMBEDDING = "embedding"
    SPEECH = "speech"
    VISION = "vision"
    TOOL = "tool"
    MEMORY = "memory"
    SEARCH = "search"



class ProviderHealth(str, Enum):
    """Health status of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderCapability:
    """A capability offered by a provider.

    Attributes:
        name: Capability identifier.
        version: Capability version.
        description: Human-readable description.
        parameters: Supported parameters.
    """

    name: str
    version: str = "1.0.0"
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)



@dataclass
class ProviderInfo:
    """Registration information for a provider.

    Attributes:
        provider_id: Unique provider identifier.
        name: Human-readable provider name.
        provider_type: Classification of the provider.
        version: Provider implementation version.
        capabilities: List of offered capabilities.
        health: Current health status.
        priority: Priority for selection (lower is preferred).
        config: Provider-specific configuration.
        registered_at: Registration timestamp.
        last_health_check: Last health check timestamp.
        metadata: Additional provider metadata.
    """

    name: str
    provider_type: ProviderType
    provider_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = "0.0.0"
    capabilities: List[ProviderCapability] = field(default_factory=list)
    health: ProviderHealth = ProviderHealth.UNKNOWN
    priority: int = 50
    config: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if the provider is in a healthy state."""
        return self.health in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED)



class Provider(ABC):
    """Abstract base class for all providers.

    All AI providers (LLM, embedding, tool, etc.) must implement
    this interface to be registered with the kernel.
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Get provider registration information."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Perform any setup needed before the provider can serve requests.

        Raises:
            RuntimeError: If initialization fails.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider gracefully.

        Release resources and close connections.
        """
        ...

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Perform a health check.

        Returns:
            Current ProviderHealth status.
        """
        ...



class ProviderRegistry(ABC):
    """Abstract interface for provider registration and discovery.

    Manages the lifecycle of providers within the kernel, including
    registration, health monitoring, and capability-based lookup.
    """

    @abstractmethod
    async def register(self, provider: Provider) -> str:
        """Register a provider with the kernel.

        Args:
            provider: The provider to register.

        Returns:
            The provider_id of the registered provider.

        Raises:
            ValueError: If a provider with the same ID exists.
        """
        ...

    @abstractmethod
    async def unregister(self, provider_id: str) -> bool:
        """Unregister a provider from the kernel.

        The provider will be shutdown before removal.

        Args:
            provider_id: The provider to remove.

        Returns:
            True if the provider was found and removed.
        """
        ...

    @abstractmethod
    async def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get a registered provider by ID.

        Args:
            provider_id: The provider identifier.

        Returns:
            Provider instance or None if not found.
        """
        ...

    @abstractmethod
    async def get_providers_by_type(
        self,
        provider_type: ProviderType,
    ) -> List[Provider]:
        """Get all providers of a specific type.

        Args:
            provider_type: The type to filter by.

        Returns:
            List of matching providers.
        """
        ...

    @abstractmethod
    async def get_providers_by_capability(
        self,
        capability_name: str,
    ) -> List[Provider]:
        """Get providers that offer a specific capability.

        Args:
            capability_name: The capability to search for.

        Returns:
            List of providers offering the capability.
        """
        ...

    @abstractmethod
    async def list_providers(self) -> List[ProviderInfo]:
        """List all registered providers.

        Returns:
            List of ProviderInfo for all registered providers.
        """
        ...

    @abstractmethod
    async def check_health_all(self) -> Dict[str, ProviderHealth]:
        """Run health checks on all registered providers.

        Returns:
            Mapping of provider IDs to their health status.
        """
        ...

    @abstractmethod
    async def get_healthy_providers(
        self,
        provider_type: Optional[ProviderType] = None,
    ) -> List[Provider]:
        """Get all healthy providers, optionally filtered by type.

        Args:
            provider_type: Optional type filter.

        Returns:
            List of healthy Provider instances.
        """
        ...
