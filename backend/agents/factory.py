"""Agent factory for creating agent instances.

Supports registration of agent classes and creation of configured
instances on demand. Enables plugin-based agent discovery.
"""

from abc import ABC, abstractmethod
from typing import Any

from agents.base import BaseAgent


class AgentFactory(ABC):
    """Abstract factory for creating agent instances.

    Manages a registry of agent classes and creates configured
    instances. Supports plugin discovery and dynamic registration.
    """

    @abstractmethod
    def register_class(
        self,
        agent_id: str,
        agent_class: type[BaseAgent],
        default_config: dict[str, Any] | None = None,
    ) -> None:
        """Register an agent class for instantiation.

        Args:
            agent_id: Identifier for this agent type.
            agent_class: The agent class to register.
            default_config: Default configuration for creation.

        Raises:
            ValueError: If already registered.
        """
        ...

    @abstractmethod
    def unregister_class(self, agent_id: str) -> bool:
        """Unregister an agent class.

        Args:
            agent_id: The agent type to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    def create(
        self,
        agent_id: str,
        config: dict[str, Any] | None = None,
    ) -> BaseAgent:
        """Create an agent instance.

        Args:
            agent_id: The agent type to instantiate.
            config: Optional configuration override.

        Returns:
            Configured BaseAgent instance.

        Raises:
            ValueError: If agent class not registered.
        """
        ...

    @abstractmethod
    def create_all(self) -> list[BaseAgent]:
        """Create instances of all registered agent types.

        Returns:
            List of configured agent instances.
        """
        ...

    @abstractmethod
    def get_registered_ids(self) -> list[str]:
        """List all registered agent type IDs.

        Returns:
            List of registered identifiers.
        """
        ...

    @abstractmethod
    def is_registered(self, agent_id: str) -> bool:
        """Check if an agent type is registered.

        Args:
            agent_id: The agent type to check.

        Returns:
            True if registered.
        """
        ...

    @abstractmethod
    def discover_plugins(self, path: str | None = None) -> int:
        """Discover and register agent plugins from a directory.

        Args:
            path: Directory to scan (uses default if None).

        Returns:
            Number of agents discovered.
        """
        ...
