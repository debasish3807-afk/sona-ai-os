"""Agent registration and discovery.

Manages the registry of available agents, supporting lookup
by ID, capability matching, and dynamic discovery.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agents.base import BaseAgent
from agents.capabilities import CapabilityRequirement
from agents.state import AgentStatus


@dataclass
class AgentEntry:
    """An entry in the agent registry.

    Attributes:
        agent: The agent instance.
        registered_at: Registration timestamp.
        enabled: Whether the agent is active.
        priority: Selection priority (lower preferred).
        metadata: Additional entry metadata.
    """

    agent: BaseAgent
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    enabled: bool = True
    priority: int = 50
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self.agent.info.agent_id

    @property
    def is_available(self) -> bool:
        """Check if this agent is available for work."""
        return self.enabled and self.agent.status in (
            AgentStatus.IDLE,
            AgentStatus.BUSY,
        )


class AgentRegistry(ABC):
    """Abstract interface for agent registration and discovery.

    Manages the lifecycle of agent registrations including
    adding, removing, and querying agents.
    """

    @abstractmethod
    async def register(self, agent: BaseAgent, priority: int = 50) -> str:
        """Register an agent with the system.

        Args:
            agent: The agent to register.
            priority: Selection priority (lower preferred).

        Returns:
            The agent_id of the registered agent.

        Raises:
            ValueError: If already registered.
        """
        ...

    @abstractmethod
    async def unregister(self, agent_id: str) -> bool:
        """Unregister an agent.

        Args:
            agent_id: The agent to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    async def get(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID.

        Args:
            agent_id: The agent identifier.

        Returns:
            BaseAgent or None.
        """
        ...

    @abstractmethod
    async def get_entry(self, agent_id: str) -> AgentEntry | None:
        """Get the full registry entry.

        Args:
            agent_id: The agent identifier.

        Returns:
            AgentEntry or None.
        """
        ...

    @abstractmethod
    async def list_all(self) -> list[AgentEntry]:
        """List all registered agents."""
        ...

    @abstractmethod
    async def list_available(self) -> list[BaseAgent]:
        """List all available (enabled + running) agents."""
        ...

    @abstractmethod
    async def find_by_capability(self, requirement: CapabilityRequirement) -> list[BaseAgent]:
        """Find agents matching capability requirements.

        Args:
            requirement: The requirements to match.

        Returns:
            Matching agents ordered by priority.
        """
        ...

    @abstractmethod
    async def find_by_tag(self, tag: str) -> list[BaseAgent]:
        """Find agents with a specific tag.

        Args:
            tag: The tag to search for.

        Returns:
            List of matching agents.
        """
        ...

    @abstractmethod
    async def set_enabled(self, agent_id: str, enabled: bool) -> None:
        """Enable or disable an agent."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Get total registered agents."""
        ...
