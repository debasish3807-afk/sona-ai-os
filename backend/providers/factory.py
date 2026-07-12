"""Provider factory for creating provider instances.

Creates and configures provider instances based on configuration.
Supports automatic discovery and instantiation of available providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from providers.base import BaseProvider
from providers.config import ProviderConfig
from providers.types import ProviderID



class ProviderFactory(ABC):
    """Abstract factory for creating provider instances.

    Maintains a registry of provider classes and creates configured
    instances on demand. Supports automatic detection of available
    providers based on environment configuration.
    """

    @abstractmethod
    def register_class(
        self,
        provider_id: ProviderID,
        provider_class: Type[BaseProvider],
    ) -> None:
        """Register a provider class for instantiation.

        Args:
            provider_id: The provider identifier.
            provider_class: The provider class to register.

        Raises:
            ValueError: If already registered.
        """
        ...

    @abstractmethod
    def unregister_class(self, provider_id: ProviderID) -> bool:
        """Unregister a provider class.

        Args:
            provider_id: The provider to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    def create(
        self,
        provider_id: ProviderID,
        config: Optional[ProviderConfig] = None,
    ) -> BaseProvider:
        """Create a provider instance.

        Uses registered class and provided or default configuration.

        Args:
            provider_id: The provider to instantiate.
            config: Optional configuration override.

        Returns:
            Configured BaseProvider instance.

        Raises:
            ValueError: If provider class not registered.
        """
        ...

    @abstractmethod
    def create_all_available(self) -> List[BaseProvider]:
        """Create instances of all providers with valid configuration.

        Checks environment for required API keys and creates
        instances only for providers that are properly configured.

        Returns:
            List of configured provider instances.
        """
        ...

    @abstractmethod
    def get_registered_providers(self) -> List[ProviderID]:
        """List all registered provider IDs.

        Returns:
            List of registered provider identifiers.
        """
        ...

    @abstractmethod
    def is_registered(self, provider_id: ProviderID) -> bool:
        """Check if a provider class is registered.

        Args:
            provider_id: The provider to check.

        Returns:
            True if the provider class is registered.
        """
        ...

    @abstractmethod
    def is_configured(self, provider_id: ProviderID) -> bool:
        """Check if a provider has valid configuration.

        Verifies that required environment variables (API keys)
        are present.

        Args:
            provider_id: The provider to check.

        Returns:
            True if properly configured.
        """
        ...

    @abstractmethod
    def get_config(self, provider_id: ProviderID) -> Optional[ProviderConfig]:
        """Get the configuration for a provider.

        Args:
            provider_id: The provider identifier.

        Returns:
            ProviderConfig or None if not configured.
        """
        ...
