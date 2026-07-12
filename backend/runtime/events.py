"""Event definitions for the Runtime & Autonomous Workflow Engine."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuntimeEventType(str, Enum):
    """Types of events emitted by the runtime engine."""

    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_QUEUED = "workflow_queued"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    TASK_QUEUED = "task_queued"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRIED = "task_retried"
    WORKER_ALLOCATED = "worker_allocated"
    WORKER_RELEASED = "worker_released"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_LOADED = "checkpoint_loaded"
    ROLLBACK_STARTED = "rollback_started"
    ROLLBACK_COMPLETED = "rollback_completed"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    WORKFLOW_COMPLETED = "workflow_completed"


@dataclass
class RuntimeEvent:
    """An event emitted during workflow execution."""

    event_type: RuntimeEventType
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
