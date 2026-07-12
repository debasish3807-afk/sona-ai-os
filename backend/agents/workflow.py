"""Workflow engine for multi-agent task execution.

Manages the definition and execution of multi-step workflows
that coordinate multiple agents in complex task sequences.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from agents.context import ExecutionResult


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A step within a workflow.

    Attributes:
        step_id: Unique step identifier.
        name: Human-readable step name.
        agent_id: Agent to execute this step.
        input_mapping: How to map workflow state to step input.
        output_mapping: How to map step output to workflow state.
        depends_on: Steps that must complete before this one.
        condition: Optional condition for execution.
        on_failure: Behavior on failure (retry|skip|abort).
        max_retries: Maximum retry attempts.
        timeout_seconds: Step timeout.
        metadata: Additional step metadata.
    """

    name: str
    agent_id: str
    step_id: str = field(default_factory=lambda: str(uuid4()))
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_mapping: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None
    on_failure: str = "abort"
    max_retries: int = 1
    timeout_seconds: float = 120.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Definition of a multi-agent workflow.

    Attributes:
        workflow_id: Unique workflow identifier.
        name: Human-readable workflow name.
        description: What this workflow accomplishes.
        steps: Ordered list of workflow steps.
        initial_state: Starting state for the workflow.
        version: Workflow definition version.
        metadata: Additional workflow metadata.
    """

    name: str
    steps: list[WorkflowStep]
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    initial_state: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """A running instance of a workflow.

    Attributes:
        execution_id: Unique execution identifier.
        workflow_id: The workflow being executed.
        status: Current execution status.
        current_step: Currently executing step ID.
        state: Current workflow state.
        step_results: Results from completed steps.
        started_at: Execution start time.
        error: Error details if failed.
        metadata: Additional execution metadata.
    """

    workflow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, ExecutionResult] = field(default_factory=dict)
    started_at: str | None = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowEngine(ABC):
    """Abstract interface for workflow execution.

    Manages the definition, execution, and monitoring of
    multi-agent workflows.
    """

    @abstractmethod
    async def register_workflow(self, definition: WorkflowDefinition) -> str:
        """Register a workflow definition.

        Args:
            definition: The workflow to register.

        Returns:
            The workflow_id.
        """
        ...

    @abstractmethod
    async def execute(
        self,
        workflow_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """Start executing a workflow.

        Args:
            workflow_id: The workflow to execute.
            initial_state: Optional state override.

        Returns:
            WorkflowExecution tracking the run.
        """
        ...

    @abstractmethod
    async def pause(self, execution_id: str) -> bool:
        """Pause a running workflow.

        Args:
            execution_id: The execution to pause.

        Returns:
            True if paused.
        """
        ...

    @abstractmethod
    async def resume(self, execution_id: str) -> bool:
        """Resume a paused workflow.

        Args:
            execution_id: The execution to resume.

        Returns:
            True if resumed.
        """
        ...

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """Cancel a workflow execution.

        Args:
            execution_id: The execution to cancel.

        Returns:
            True if cancelled.
        """
        ...

    @abstractmethod
    async def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        """Get workflow execution status.

        Args:
            execution_id: The execution to query.

        Returns:
            WorkflowExecution or None.
        """
        ...

    @abstractmethod
    async def list_workflows(self) -> list[WorkflowDefinition]:
        """List all registered workflow definitions."""
        ...

    @abstractmethod
    async def list_executions(self, workflow_id: str | None = None) -> list[WorkflowExecution]:
        """List workflow executions.

        Args:
            workflow_id: Optional filter by workflow.

        Returns:
            List of executions.
        """
        ...

    @abstractmethod
    async def validate_workflow(self, definition: WorkflowDefinition) -> list[str]:
        """Validate a workflow definition.

        Args:
            definition: The workflow to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        ...
