"""Job schemas for background execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any
from uuid import uuid4


class JobState(StrEnum):
    """Possible states for a background job."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class JobPriority(IntEnum):
    """Priority levels for job scheduling."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Job:
    """Represents a background job."""

    name: str
    handler: str
    job_id: str = field(default_factory=lambda: str(uuid4()))
    params: dict[str, Any] = field(default_factory=dict)
    state: JobState = JobState.PENDING
    priority: JobPriority = JobPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary representation."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "handler": self.handler,
            "params": self.params,
            "state": self.state.value,
            "priority": self.priority.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": (self.scheduled_at.isoformat() if self.scheduled_at else None),
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "error": self.error,
        }
