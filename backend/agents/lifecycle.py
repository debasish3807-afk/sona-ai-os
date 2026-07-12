"""Agent lifecycle management.

Manages the initialization, startup, shutdown, and dependency
resolution for agents. Ensures proper ordering based on the
agent dependency graph.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from agents.state import AgentHealth, AgentStatus


@dataclass
class DependencyNode:
    """A node in the agent dependency graph.

    Attributes:
        agent_id: The agent identifier.
        dependencies: Agent IDs this agent depends on.
        dependents: Agent IDs that depend on this agent.
    """

    agent_id: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)


@dataclass
class LifecycleResult:
    """Result of a lifecycle operation on an agent.

    Attributes:
        agent_id: The agent that was operated on.
        success: Whether the operation succeeded.
        status: Resulting agent status.
        error: Error message if failed.
        duration_ms: Operation duration in milliseconds.
    """

    agent_id: str
    success: bool
    status: AgentStatus
    error: str | None = None
    duration_ms: float = 0.0


class AgentLifecycleManager(ABC):
    """Abstract interface for agent lifecycle management.

    Coordinates lifecycle transitions for all agents respecting
    their dependency relationships.
    """

    @abstractmethod
    async def initialize_agent(self, agent_id: str) -> LifecycleResult:
        """Initialize a specific agent.

        Ensures dependencies are initialized first.

        Args:
            agent_id: The agent to initialize.

        Returns:
            LifecycleResult with outcome.
        """
        ...

    @abstractmethod
    async def start_agent(self, agent_id: str) -> LifecycleResult:
        """Start a specific agent.

        Ensures dependencies are started first.

        Args:
            agent_id: The agent to start.

        Returns:
            LifecycleResult with outcome.
        """
        ...

    @abstractmethod
    async def stop_agent(self, agent_id: str) -> LifecycleResult:
        """Stop a specific agent.

        Stops dependents first, then the target agent.

        Args:
            agent_id: The agent to stop.

        Returns:
            LifecycleResult with outcome.
        """
        ...

    @abstractmethod
    async def restart_agent(self, agent_id: str) -> LifecycleResult:
        """Restart an agent (stop + start).

        Args:
            agent_id: The agent to restart.

        Returns:
            LifecycleResult with outcome.
        """
        ...

    @abstractmethod
    async def start_all(self) -> dict[str, LifecycleResult]:
        """Start all registered agents in dependency order.

        Returns:
            Mapping of agent IDs to their lifecycle results.
        """
        ...

    @abstractmethod
    async def stop_all(self) -> dict[str, LifecycleResult]:
        """Stop all agents in reverse dependency order.

        Returns:
            Mapping of agent IDs to their lifecycle results.
        """
        ...

    @abstractmethod
    async def health_check_all(self) -> dict[str, AgentHealth]:
        """Run health checks on all agents.

        Returns:
            Mapping of agent IDs to their health status.
        """
        ...

    @abstractmethod
    def get_dependency_graph(self) -> dict[str, DependencyNode]:
        """Get the full agent dependency graph.

        Returns:
            Mapping of agent IDs to their dependency nodes.
        """
        ...

    @abstractmethod
    def get_startup_order(self) -> list[str]:
        """Get the topologically-sorted startup order.

        Returns:
            Ordered list of agent IDs for startup.
        """
        ...

    @abstractmethod
    def validate_dependencies(self) -> list[str]:
        """Validate the dependency graph for cycles and missing deps.

        Returns:
            List of validation error messages (empty if valid).
        """
        ...
