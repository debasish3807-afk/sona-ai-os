"""Abstract agent interface.

Defines the base contract that all agents must implement.
This is the fundamental building block of the multi-agent system.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from agents.capabilities import AgentCapabilitySet
from agents.context import ExecutionContext, ExecutionResult
from agents.state import AgentHealth, AgentStatus


@dataclass
class AgentInfo:
    """Static metadata about an agent.

    Attributes:
        agent_id: Unique agent identifier.
        name: Human-readable agent name.
        description: What this agent does.
        version: Agent implementation version.
        author: Agent author/owner.
        tags: Categorization tags.
        max_concurrent_tasks: Max parallel tasks.
        priority: Default execution priority.
        metadata: Additional agent metadata.
    """

    agent_id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = "Sona AI OS"
    tags: list[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    priority: int = 50
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Every agent in Sona AI OS must implement this interface to
    participate in the multi-agent system. Provides lifecycle
    management, task execution, health monitoring, and capability
    declaration.
    """

    @property
    @abstractmethod
    def info(self) -> AgentInfo:
        """Get static agent metadata."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> AgentCapabilitySet:
        """Get declared capabilities of this agent."""
        ...

    @property
    @abstractmethod
    def status(self) -> AgentStatus:
        """Get current operational status."""
        ...

    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """Get list of agent IDs this agent depends on.

        Dependencies are started before this agent and stopped after.

        Returns:
            List of required agent identifiers.
        """
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent.

        Load configuration, set up resources, and validate
        prerequisites. Called once before start().

        Raises:
            AgentInitializationError: If initialization fails.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the agent and begin accepting tasks.

        Transition from initialized to active state.

        Raises:
            AgentError: If the agent cannot start.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent gracefully.

        Complete in-progress tasks and release resources.
        Must be idempotent.
        """
        ...

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute a task within the given context.

        This is the primary work method. The agent processes the
        task described in the context and returns a result.

        Args:
            context: Execution context with task details.

        Returns:
            ExecutionResult with output or error.

        Raises:
            AgentExecutionError: On unrecoverable execution failure.
            AgentTimeoutError: If execution exceeds timeout.
        """
        ...

    @abstractmethod
    def execute_stream(self, context: ExecutionContext) -> AsyncIterator[dict[str, Any]]:
        """Execute a task with streaming output.

        For tasks that benefit from incremental results.

        Args:
            context: Execution context with task details.

        Yields:
            Incremental result chunks.
        """
        ...

    # ------------------------------------------------------------------
    # Health & Monitoring
    # ------------------------------------------------------------------

    @abstractmethod
    async def health(self) -> AgentHealth:
        """Perform a health check.

        Returns:
            Current health status.
        """
        ...

    # ------------------------------------------------------------------
    # Optional hooks
    # ------------------------------------------------------------------

    async def on_error(self, error: Exception, context: ExecutionContext | None = None) -> None:
        """Hook called when an error occurs during execution.

        Override for custom error handling, logging, or recovery.

        Args:
            error: The exception that occurred.
            context: The execution context (if available).
        """
        pass

    async def on_task_delegated(self, target_agent_id: str, context: ExecutionContext) -> None:
        """Hook called when this agent delegates to another.

        Args:
            target_agent_id: The agent receiving the delegation.
            context: The delegated execution context.
        """
        pass
