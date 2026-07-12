"""Task planning interface.

Provides intelligent decomposition of complex tasks into
subtasks, plans execution strategies, and determines agent
assignments.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class PlanStatus(str, Enum):
    """Status of an execution plan."""

    DRAFT = "draft"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Types of plan steps."""

    EXECUTE = "execute"
    DELEGATE = "delegate"
    PARALLEL = "parallel"
    CONDITION = "condition"
    LOOP = "loop"
    WAIT = "wait"
    AGGREGATE = "aggregate"


@dataclass
class PlanStep:
    """A single step in an execution plan.

    Attributes:
        step_id: Unique step identifier.
        step_type: The type of step.
        agent_id: Target agent for this step.
        input_data: Input for this step.
        depends_on: Step IDs that must complete first.
        timeout_seconds: Maximum step duration.
        retry_count: Number of retries on failure.
        metadata: Additional step metadata.
    """

    step_type: StepType
    step_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: float = 120.0
    retry_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """A complete plan for executing a complex task.

    Attributes:
        plan_id: Unique plan identifier.
        task_description: What the plan accomplishes.
        steps: Ordered list of steps.
        status: Current plan status.
        estimated_duration_ms: Estimated total duration.
        metadata: Additional plan metadata.
    """

    task_description: str
    steps: list[PlanStep]
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    status: PlanStatus = PlanStatus.DRAFT
    estimated_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        """Get the number of steps."""
        return len(self.steps)

    @property
    def is_complete(self) -> bool:
        """Check if the plan is in a terminal state."""
        return self.status in (
            PlanStatus.COMPLETED,
            PlanStatus.FAILED,
            PlanStatus.CANCELLED,
        )


class TaskPlanner(ABC):
    """Abstract interface for task planning.

    Decomposes complex tasks into executable plans with
    step ordering, agent assignment, and dependency management.
    """

    @abstractmethod
    async def create_plan(
        self,
        task_description: str,
        context: dict[str, Any],
        available_agents: list[str] | None = None,
    ) -> ExecutionPlan:
        """Create an execution plan for a task.

        Analyzes the task and decomposes it into ordered steps
        with appropriate agent assignments.

        Args:
            task_description: What needs to be accomplished.
            context: Additional context for planning.
            available_agents: Optional constraint on agents to use.

        Returns:
            ExecutionPlan with steps and assignments.
        """
        ...

    @abstractmethod
    async def validate_plan(self, plan: ExecutionPlan) -> list[str]:
        """Validate a plan for correctness.

        Checks for dependency cycles, missing agents,
        and logical consistency.

        Args:
            plan: The plan to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        ...

    @abstractmethod
    async def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize a plan for efficiency.

        Identifies parallelizable steps and minimizes
        overall execution time.

        Args:
            plan: The plan to optimize.

        Returns:
            Optimized plan.
        """
        ...

    @abstractmethod
    async def revise_plan(
        self,
        plan: ExecutionPlan,
        feedback: dict[str, Any],
    ) -> ExecutionPlan:
        """Revise a plan based on execution feedback.

        Called when a step fails and replanning is needed.

        Args:
            plan: The current plan.
            feedback: Failure details and context.

        Returns:
            Revised plan.
        """
        ...

    @abstractmethod
    async def estimate_duration(self, plan: ExecutionPlan) -> float:
        """Estimate total plan execution duration.

        Args:
            plan: The plan to estimate.

        Returns:
            Estimated duration in milliseconds.
        """
        ...
