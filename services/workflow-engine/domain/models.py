"""Domain models for the Workflow Engine service.

Defines the data structures used by the Workflow Engine for workflow
definition, step execution, and workflow lifecycle management.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class StepStatus(StrEnum):
    """Enumeration of possible workflow step execution states.

    Tracks the current lifecycle status of a workflow step or
    an overall workflow execution.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting_for_input"


@dataclass(frozen=True)
class WorkflowStep:
    """A single step within a workflow definition.

    Attributes:
        step_id: Unique identifier for this step within the workflow.
        name: Human-readable name for the step.
        action: The action to perform (e.g., agent call, API request).
        params: Parameters to pass to the action handler.
        depends_on: List of step_ids that must complete before this step runs.
        retry_count: Maximum number of retry attempts on failure.
        timeout_seconds: Maximum time allowed for step execution.
        condition: Optional condition expression for conditional execution.
    """

    step_id: str
    name: str
    action: str
    params: dict[str, Any]
    depends_on: list[str] = ()
    retry_count: int = 3
    timeout_seconds: int = 300
    condition: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    """A complete workflow definition containing ordered steps.

    Attributes:
        workflow_id: Unique identifier for this workflow definition.
        name: Human-readable name for the workflow.
        description: Detailed description of what the workflow accomplishes.
        steps: Ordered list of workflow steps to execute.
        trigger: Optional event trigger that starts this workflow automatically.
        schedule: Optional cron-like schedule expression for periodic execution.
    """

    workflow_id: str
    name: str
    description: str
    steps: list[WorkflowStep] = ()
    trigger: str | None = None
    schedule: str | None = None


@dataclass
class WorkflowExecution:
    """Represents the runtime state of a workflow execution.

    Unlike WorkflowDefinition and WorkflowStep, this is mutable since
    execution state changes as the workflow progresses.

    Attributes:
        execution_id: Unique identifier for this execution instance.
        workflow_id: Reference to the workflow definition being executed.
        status: Current status of the overall execution.
        current_step: The step_id of the currently executing step, if any.
        results: Mapping of step_id to step execution results.
        started_at: ISO 8601 timestamp when execution began.
        completed_at: ISO 8601 timestamp when execution finished.
    """

    execution_id: str
    workflow_id: str
    status: StepStatus
    current_step: str | None = None
    results: dict[str, Any] | None = None
    started_at: str | None = None
    completed_at: str | None = None
