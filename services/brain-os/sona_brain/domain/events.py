"""Brain OS domain events.

Events emitted during plan execution to enable observability,
audit trails, and event-driven integrations.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class ExecutionStartedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a plan begins execution.

    Attributes:
        plan_id: Identifier of the plan being executed.
        intent: The classified intent driving this execution.
        steps_count: Total number of steps in the plan.
    """

    plan_id: str = ""
    intent: str = ""
    steps_count: int = 0


@dataclass(frozen=True)
class StepCompletedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an individual step completes successfully.

    Attributes:
        plan_id: Identifier of the parent plan.
        step_id: Identifier of the completed step.
        step_type: Type of step that completed.
        latency_ms: Execution latency in milliseconds.
    """

    plan_id: str = ""
    step_id: str = ""
    step_type: str = ""
    latency_ms: float = 0.0


@dataclass(frozen=True)
class StepFailedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a step fails execution.

    Attributes:
        plan_id: Identifier of the parent plan.
        step_id: Identifier of the failed step.
        error: Error description.
        retryable: Whether the step can be retried.
    """

    plan_id: str = ""
    step_id: str = ""
    error: str = ""
    retryable: bool = False


@dataclass(frozen=True)
class ExecutionCompletedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a plan completes execution successfully.

    Attributes:
        plan_id: Identifier of the completed plan.
        total_latency_ms: Total execution time in milliseconds.
        tokens_in: Total input tokens consumed.
        tokens_out: Total output tokens generated.
    """

    plan_id: str = ""
    total_latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True)
class ExecutionFailedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a plan fails execution.

    Attributes:
        plan_id: Identifier of the failed plan.
        error: Error description.
        steps_completed: Number of steps that completed before failure.
    """

    plan_id: str = ""
    error: str = ""
    steps_completed: int = 0
