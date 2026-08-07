"""THALAMUS domain events.

Events emitted during the routing lifecycle to enable observability,
auditing, and reactive downstream processing.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class IntentClassifiedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an intent has been successfully classified.

    Attributes:
        content: The original user input that was classified.
        intent: The resulting IntentCategory value.
        confidence: Classification confidence score (0.0-1.0).
    """

    content: str = ""
    intent: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class ExecutionPlanCreatedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an execution plan has been successfully created.

    Attributes:
        plan_id: Unique identifier for the created plan.
        intent: The classified intent that drove plan creation.
        model_id: The model selected for the primary LLM call.
        steps_count: Number of execution steps in the plan.
    """

    plan_id: str = ""
    intent: str = ""
    model_id: str = ""
    steps_count: int = 0


@dataclass(frozen=True)
class RoutingFailedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when routing fails for any reason.

    Attributes:
        content: The original user input that failed to route.
        error: Description of the failure.
    """

    content: str = ""
    error: str = ""
