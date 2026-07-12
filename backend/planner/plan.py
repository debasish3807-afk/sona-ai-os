"""Execution plan data structures.

Defines the plan, steps, and status tracking for multi-step
tool execution workflows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    """Status of a single execution step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class PlanStatus(str, Enum):
    """Overall status of an execution plan."""

    CREATED = "created"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


@dataclass
class PlanStep:
    """A single step in an execution plan.

    Each step maps to a single tool invocation with specific parameters.
    Steps can depend on previous step outputs.
    """

    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str = ""
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # step_ids
    status: StepStatus = StepStatus.PENDING
    result_output: str = ""
    result_error: str | None = None
    duration_ms: float = 0.0
    retry_count: int = 0
    max_retries: int = 1
    condition: str | None = None  # Skip condition (e.g., "previous_success")

    def mark_running(self) -> None:
        """Mark step as currently executing."""
        self.status = StepStatus.RUNNING

    def mark_completed(self, output: str, duration_ms: float) -> None:
        """Mark step as successfully completed."""
        self.status = StepStatus.COMPLETED
        self.result_output = output
        self.duration_ms = duration_ms

    def mark_failed(self, error: str, duration_ms: float) -> None:
        """Mark step as failed."""
        self.status = StepStatus.FAILED
        self.result_error = error
        self.duration_ms = duration_ms

    def mark_skipped(self, reason: str) -> None:
        """Mark step as skipped."""
        self.status = StepStatus.SKIPPED
        self.result_error = reason

    @property
    def is_terminal(self) -> bool:
        """Whether step is in a final state."""
        return self.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)

    def to_dict(self) -> dict[str, Any]:
        """Serialize step to dictionary."""
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "description": self.description,
            "params": self.params,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result_output": self.result_output[:500] if self.result_output else "",
            "result_error": self.result_error,
            "duration_ms": round(self.duration_ms, 2),
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutionPlan:
    """A complete execution plan with ordered steps.

    Plans represent multi-step workflows that the AI has decomposed
    from a user request. Steps are executed sequentially with
    dependency tracking.
    """

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.CREATED
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.FAILED)

    @property
    def progress_pct(self) -> float:
        if not self.steps:
            return 0.0
        terminal = sum(1 for s in self.steps if s.is_terminal)
        return (terminal / len(self.steps)) * 100

    def add_step(
        self,
        tool_name: str,
        description: str,
        params: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
    ) -> PlanStep:
        """Add a new step to the plan."""
        step = PlanStep(
            tool_name=tool_name,
            description=description,
            params=params or {},
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        return step

    def get_next_step(self) -> PlanStep | None:
        """Get the next step ready for execution.

        A step is ready when all its dependencies are completed.
        """
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            # Check dependencies
            deps_met = all(
                any(s.step_id == dep and s.status == StepStatus.COMPLETED for s in self.steps)
                for dep in step.depends_on
            )
            if deps_met or not step.depends_on:
                return step
        return None

    def finalize(self) -> None:
        """Mark plan as completed or partially completed."""
        self.completed_at = datetime.now(UTC).isoformat()
        if self.failed_count == 0:
            self.status = PlanStatus.COMPLETED
        elif self.completed_count > 0:
            self.status = PlanStatus.PARTIALLY_COMPLETED
        else:
            self.status = PlanStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        """Serialize plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "step_count": self.step_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "progress_pct": round(self.progress_pct, 1),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }
