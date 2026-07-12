"""Agent state management.

Tracks and manages the operational state of individual agents
and the agent system as a whole.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    """Operational status of an agent."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AgentHealth(str, Enum):
    """Health status of an agent."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Runtime metrics for an agent.

    Attributes:
        tasks_completed: Number of tasks successfully completed.
        tasks_failed: Number of tasks that failed.
        total_execution_ms: Cumulative execution time.
        avg_execution_ms: Average task execution time.
        current_tasks: Number of tasks currently executing.
        queued_tasks: Number of tasks waiting.
        last_active: Timestamp of last activity.
    """

    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_ms: float = 0.0
    avg_execution_ms: float = 0.0
    current_tasks: int = 0
    queued_tasks: int = 0
    last_active: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 1.0
        return self.tasks_completed / total


@dataclass
class AgentState:
    """Complete state snapshot for an agent.

    Attributes:
        agent_id: Agent identifier.
        status: Current operational status.
        health: Current health status.
        metrics: Runtime performance metrics.
        started_at: When the agent was started.
        last_updated: Last state update timestamp.
        error_message: Current error (if in ERROR state).
        metadata: Additional state metadata.
    """

    agent_id: str
    status: AgentStatus = AgentStatus.UNINITIALIZED
    health: AgentHealth = AgentHealth.UNKNOWN
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    started_at: datetime | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if the agent is available for work."""
        return self.status in (AgentStatus.IDLE, AgentStatus.BUSY)

    @property
    def is_running(self) -> bool:
        """Check if the agent is in a running state."""
        return self.status in (
            AgentStatus.IDLE,
            AgentStatus.BUSY,
            AgentStatus.DEGRADED,
        )


class AgentStateManager(ABC):
    """Abstract interface for agent state tracking.

    Manages state transitions, metrics recording, and state
    queries across all agents in the system.
    """

    @abstractmethod
    async def get_state(self, agent_id: str) -> AgentState | None:
        """Get the current state of an agent."""
        ...

    @abstractmethod
    async def set_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update an agent's operational status."""
        ...

    @abstractmethod
    async def set_health(self, agent_id: str, health: AgentHealth) -> None:
        """Update an agent's health status."""
        ...

    @abstractmethod
    async def record_task_completion(
        self, agent_id: str, execution_ms: float, success: bool
    ) -> None:
        """Record a task completion for metrics."""
        ...

    @abstractmethod
    async def get_all_states(self) -> list[AgentState]:
        """Get states of all registered agents."""
        ...

    @abstractmethod
    async def get_available_agents(self) -> list[str]:
        """Get IDs of agents available for work."""
        ...

    @abstractmethod
    async def reset_metrics(self, agent_id: str) -> None:
        """Reset metrics for an agent."""
        ...
