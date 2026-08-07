"""Brain OS execution domain models.

Defines the runtime state tracking for execution plans, including
per-step results and overall execution context.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class StepState(StrEnum):
    """Possible states for an individual execution step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ExecutionState(StrEnum):
    """Possible states for the overall execution."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REPLANNING = "replanning"


@dataclass
class StepResult:
    """Result of executing a single step.

    Attributes:
        step_id: Identifier of the step that produced this result.
        state: Current state of the step.
        output: Output data from step execution.
        error: Error message if step failed.
        latency_ms: Execution time in milliseconds.
        retry_count: Number of retry attempts made.
        started_at: When the step started executing.
        completed_at: When the step finished.
    """

    step_id: str
    state: StepState
    output: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ExecutionContext:
    """Tracks the full state of an execution plan's runtime.

    Attributes:
        plan_id: Identifier of the execution plan being executed.
        state: Current overall execution state.
        step_results: Map of step_id to StepResult for completed/running steps.
        final_output: The aggregated final response content.
        total_latency_ms: Total wall-clock latency in milliseconds.
        total_tokens_in: Total input tokens consumed across all LLM steps.
        total_tokens_out: Total output tokens generated across all LLM steps.
        model_used: Primary model used for generation.
        errors: List of error messages encountered during execution.
        metadata: Additional metadata about the execution.
        created_at: When the execution context was created.
        completed_at: When the execution finished.
    """

    plan_id: str
    state: ExecutionState = ExecutionState.CREATED
    step_results: dict[str, StepResult] = field(default_factory=dict)
    final_output: str = ""
    total_latency_ms: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    model_used: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
