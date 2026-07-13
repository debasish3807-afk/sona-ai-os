"""Agent event system for decoupled communication and monitoring."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentEventType(str, Enum):
    """Types of events emitted by the agent system."""

    CREATED = "agent.created"
    STARTED = "agent.started"
    COMPLETED = "agent.completed"
    FAILED = "agent.failed"
    PAUSED = "agent.paused"
    RESUMED = "agent.resumed"
    TERMINATED = "agent.terminated"
    MESSAGE_SENT = "agent.message_sent"
    MESSAGE_RECEIVED = "agent.message_received"
    TASK_ASSIGNED = "agent.task_assigned"
    TASK_COMPLETED = "agent.task_completed"
    CONSENSUS_REACHED = "agent.consensus_reached"
    NEGOTIATION_STARTED = "agent.negotiation_started"
    NEGOTIATION_COMPLETED = "agent.negotiation_completed"
    CHECKPOINT_CREATED = "agent.checkpoint_created"
    RECOVERY_STARTED = "agent.recovery_started"


@dataclass
class AgentEvent:
    """An event emitted by the agent system."""

    event_type: AgentEventType
    agent_id: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
