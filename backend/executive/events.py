"""Executive Intelligence layer — event system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class ExecutiveEventType(str, Enum):
    """Types of events emitted by the executive layer."""

    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    STRATEGY_GENERATED = "strategy_generated"
    STRATEGY_SELECTED = "strategy_selected"
    DECISION_MADE = "decision_made"
    EXECUTION_PLANNED = "execution_planned"
    EXECUTION_APPROVED = "execution_approved"
    EXECUTION_REJECTED = "execution_rejected"
    EXECUTION_OPTIMIZED = "execution_optimized"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    FAILURE_DETECTED = "failure_detected"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"


@dataclass
class ExecutiveEvent:
    """An event emitted during executive processing."""

    event_type: ExecutiveEventType
    goal_id: str
    data: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "goal_id": self.goal_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
