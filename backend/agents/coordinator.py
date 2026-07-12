"""Multi-agent coordination.

Manages the collaboration between multiple agents working on
related tasks. Handles task delegation, result aggregation,
conflict resolution, and parallel execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from agents.context import ExecutionContext, ExecutionResult


class CoordinationMode(str, Enum):
    """Modes for multi-agent coordination."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    COMPETITIVE = "competitive"
    COLLABORATIVE = "collaborative"


class DelegationStatus(str, Enum):
    """Status of a delegated task."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DelegationRequest:
    """Request to delegate work to another agent.

    Attributes:
        delegation_id: Unique delegation identifier.
        source_agent_id: Agent delegating the work.
        target_agent_id: Target agent (or None for auto-select).
        context: Execution context for the delegated task.
        priority: Delegation priority.
        timeout_seconds: Max time for the delegation.
        fallback_agents: Backup agents on failure.
        metadata: Additional delegation metadata.
    """

    source_agent_id: str
    context: ExecutionContext
    delegation_id: str = field(default_factory=lambda: str(uuid4()))
    target_agent_id: str | None = None
    priority: int = 50
    timeout_seconds: float = 120.0
    fallback_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DelegationResult:
    """Result of a delegated task.

    Attributes:
        delegation_id: The delegation identifier.
        status: Final delegation status.
        result: Execution result (if completed).
        agent_id: The agent that executed.
        duration_ms: Total delegation duration.
        attempts: Number of attempts made.
        metadata: Additional result metadata.
    """

    delegation_id: str
    status: DelegationStatus
    result: ExecutionResult | None = None
    agent_id: str | None = None
    duration_ms: float = 0.0
    attempts: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationPlan:
    """Plan for coordinating multiple agents.

    Attributes:
        plan_id: Unique plan identifier.
        mode: Coordination mode.
        agents: Agents involved in this coordination.
        steps: Ordered execution steps.
        shared_state: Shared state between agents.
        metadata: Additional plan metadata.
    """

    mode: CoordinationMode
    agents: list[str]
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    steps: list[dict[str, Any]] = field(default_factory=list)
    shared_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentCoordinator(ABC):
    """Abstract interface for multi-agent coordination.

    Orchestrates collaboration between agents through delegation,
    parallel execution, and result aggregation.
    """

    @abstractmethod
    async def delegate(self, request: DelegationRequest) -> DelegationResult:
        """Delegate a task to another agent.

        Handles agent selection, execution monitoring, fallback,
        and result collection.

        Args:
            request: The delegation request.

        Returns:
            DelegationResult with execution outcome.
        """
        ...

    @abstractmethod
    async def execute_parallel(
        self,
        contexts: list[ExecutionContext],
        agents: list[str] | None = None,
    ) -> list[ExecutionResult]:
        """Execute tasks in parallel across multiple agents.

        Args:
            contexts: Execution contexts for each task.
            agents: Optional specific agents to use.

        Returns:
            List of results (one per context).
        """
        ...

    @abstractmethod
    async def execute_pipeline(
        self,
        initial_context: ExecutionContext,
        pipeline: list[str],
    ) -> ExecutionResult:
        """Execute a pipeline of agents sequentially.

        Each agent's output becomes the next agent's input.

        Args:
            initial_context: Starting context.
            pipeline: Ordered list of agent IDs.

        Returns:
            Final execution result.
        """
        ...

    @abstractmethod
    async def execute_plan(self, plan: CoordinationPlan) -> dict[str, ExecutionResult]:
        """Execute a coordination plan.

        Args:
            plan: The coordination plan to execute.

        Returns:
            Mapping of step IDs to their results.
        """
        ...

    @abstractmethod
    async def aggregate_results(
        self,
        results: list[ExecutionResult],
        strategy: str = "merge",
    ) -> ExecutionResult:
        """Aggregate results from multiple agents.

        Args:
            results: Results to aggregate.
            strategy: Aggregation strategy (merge|best|vote).

        Returns:
            Aggregated ExecutionResult.
        """
        ...

    @abstractmethod
    async def cancel_delegation(self, delegation_id: str) -> bool:
        """Cancel an in-progress delegation.

        Args:
            delegation_id: The delegation to cancel.

        Returns:
            True if cancelled.
        """
        ...

    @abstractmethod
    async def get_delegation_status(self, delegation_id: str) -> DelegationStatus | None:
        """Get the status of a delegation.

        Args:
            delegation_id: The delegation to query.

        Returns:
            Current status or None.
        """
        ...
