"""Meta Reasoning & Self Reflection Engine — event system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MetaReasoningEventType(str, Enum):
    """Types of events emitted by the meta-reasoning layer."""

    REFLECTION_STARTED = "reflection_started"
    REFLECTION_COMPLETED = "reflection_completed"
    CRITIQUE_GENERATED = "critique_generated"
    ALTERNATIVE_GENERATED = "alternative_generated"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    PLAN_VALIDATED = "plan_validated"
    PLAN_REJECTED = "plan_rejected"
    PLAN_REFINED = "plan_refined"
    EVIDENCE_VERIFIED = "evidence_verified"
    CONFIDENCE_UPDATED = "confidence_updated"
    REASONING_COMPLETED = "reasoning_completed"


@dataclass
class MetaReasoningEvent:
    """An event emitted during meta-reasoning processing."""

    event_type: MetaReasoningEventType
    plan_id: str
    data: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "plan_id": self.plan_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
