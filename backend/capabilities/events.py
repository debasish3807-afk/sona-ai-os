"""Capability events — event types and event data for the fabric."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityEventType(str, Enum):
    """Types of events emitted by the capability fabric."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVATED = "activated"
    SELECTED = "selected"
    EXECUTED = "executed"
    FAILED = "failed"
    RECOVERED = "recovered"
    UPGRADED = "upgraded"
    REMOVED = "removed"


@dataclass
class CapabilityEvent:
    """An event emitted by the capability fabric."""

    event_type: CapabilityEventType
    capability_id: str
    capability_name: str = ""
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "timestamp": self.timestamp,
            "data": self.data,
        }
