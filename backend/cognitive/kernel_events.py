"""Kernel events — strongly typed events for the cognitive pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    """All kernel event types."""

    REQUEST_STARTED = "request.started"
    INTENT_DETECTED = "intent.detected"
    GOAL_CREATED = "goal.created"
    CONTEXT_BUILT = "context.built"
    THINKING_COMPLETED = "thinking.completed"
    REASONING_COMPLETED = "reasoning.completed"
    PLANNING_COMPLETED = "planning.completed"
    DECISION_MADE = "decision.made"
    CAPABILITY_LOADED = "capability.loaded"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    VERIFICATION_COMPLETED = "verification.completed"
    LEARNING_COMPLETED = "learning.completed"
    MEMORY_STORED = "memory.stored"
    REQUEST_COMPLETED = "request.completed"
    FAILURE_OCCURRED = "failure.occurred"
    RECOVERY_STARTED = "recovery.started"
    RECOVERY_COMPLETED = "recovery.completed"
    ENGINE_REGISTERED = "engine.registered"
    ENGINE_UNREGISTERED = "engine.unregistered"
    ENGINE_HEALTH_CHANGED = "engine.health_changed"
    BUDGET_WARNING = "budget.warning"
    KERNEL_STARTED = "kernel.started"
    KERNEL_STOPPED = "kernel.stopped"


@dataclass
class KernelEvent:
    """A single kernel event with metadata."""

    event_type: EventType
    event_id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""
    engine_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: dict[str, Any] = field(default_factory=dict)
    priority: int = 50  # Lower = higher priority

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "request_id": self.request_id,
            "engine_id": self.engine_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "priority": self.priority,
        }
