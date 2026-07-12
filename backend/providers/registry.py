"""Provider registration and discovery.

Manages the registry of available providers, supporting lookup
by ID, type, and capability requirements.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from providers.base import BaseProvider
from providers.capabilities import CapabilityRequirement
from providers.health import HealthState
from providers.types import ProviderID


@dataclass
class ProviderEntry:
    """An entry in the provider registry.

    Attributes:
        provider: The provider instance.
        registered_at: Registration timestamp.
        health_state: Current health state.
        enabled: Whether the provider is enabled.
        priority: Selection priority (lower = preferred).
        metadata: Additional entry metadata.
    """

    provider: BaseProvider
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    health_state: HealthState = HealthState.UNKNOWN
    enabled: bool = True
    priority: int = 50
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def provider_id(self) -> ProviderID:
        """Get the provider ID from the provider instance."""
        return self.provider.provider_id

    @property
    def is_available(self) -> bool:
        """Check if this entry is available for use."""
        return self.enabled and self.health_state in (HealthState.HEALTHY, HealthState.DEGRADED)


class ProviderRegistry(ABC):
    """Abstract interface for provider registration and discovery.

    Manages a registry of provider instances, supporting
    registration, lookup, capability matching, and lifecycle.
    """

    @abstractmethod
    async def register(
        self,
        provider: BaseProvider,
        priority: int = 50,
    ) -> ProviderID:
        """Register a provider instance.

        Initializes the provider and adds it to the registry.

        Args:
            provider: The provider to register.
            priority: Selection priority (lower = preferred).

        Returns:
            The provider ID of the registered provider.

        Raises:
            ValueError: If already registered.
            ProviderError: If initialization fails.
        """
        ...

    @abstractmethod
    async def unregister(self, provider_id: ProviderID) -> bool:
        """Unregister and shutdown a provider.

        Args:
            provider_id: The provider to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    async def get(self, provider_id: ProviderID) -> BaseProvider | None:
        """Get a registered provider by ID.

        Args:
            provider_id: The provider identifier.

        Returns:
            BaseProvider instance or None.
        """
        ...

    @abstractmethod
    async def get_entry(self, provider_id: ProviderID) -> ProviderEntry | None:
        """Get the full registry entry for a provider.

        Args:
            provider_id: The provider identifier.

        Returns:
            ProviderEntry or None.
        """
        ...

    @abstractmethod
    async def list_all(self) -> list[ProviderEntry]:
        """List all registered provider entries.

        Returns:
            List of all ProviderEntry instances.
        """
        ...

    @abstractmethod
    async def list_available(self) -> list[BaseProvider]:
        """List all available (healthy + enabled) providers.

        Returns:
            List of available BaseProvider instances.
        """
        ...

    @abstractmethod
    async def find_by_capability(
        self,
        requirement: CapabilityRequirement,
    ) -> list[BaseProvider]:
        """Find providers matching capability requirements.

        Args:
            requirement: The capability requirements to match.

        Returns:
            List of providers satisfying the requirements,
            ordered by priority.
        """
        ...

    @abstractmethod
    async def find_by_model(self, model_id: str) -> BaseProvider | None:
        """Find the provider that serves a specific model.

        Args:
            model_id: The model identifier to look up.

        Returns:
            BaseProvider serving the model, or None.
        """
        ...

    @abstractmethod
    async def set_enabled(self, provider_id: ProviderID, enabled: bool) -> None:
        """Enable or disable a provider.

        Args:
            provider_id: The provider to update.
            enabled: New enabled state.
        """
        ...

    @abstractmethod
    async def update_health(self, provider_id: ProviderID, state: HealthState) -> None:
        """Update the health state of a provider.

        Args:
            provider_id: The provider to update.
            state: New health state.
        """
        ...

    @abstractmethod
    async def get_by_priority(self) -> list[BaseProvider]:
        """Get all available providers ordered by priority.

        Returns:
            Providers sorted by priority (lowest first).
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """Get the number of registered providers.

        Returns:
            Total registered provider count.
        """
        ...
