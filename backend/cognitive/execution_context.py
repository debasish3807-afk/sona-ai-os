"""Execution Context — tracks execution state, retries, rollback points."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionState(str, Enum):
    """States of request execution through the pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


@dataclass
class CheckpointData:
    """A saved checkpoint for recovery."""

    checkpoint_id: str = ""
    engine_id: str = ""
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionContext:
    """Tracks execution state through the kernel pipeline.

    Manages retries, rollback points, cancellation, checkpoints,
    and the execution timeline for observability.
    """

    # State
    state: ExecutionState = ExecutionState.PENDING
    started_at: float = 0.0
    completed_at: float = 0.0

    # Progress
    completed_engines: list[str] = field(default_factory=list)
    current_engine: str = ""
    pending_engines: list[str] = field(default_factory=list)

    # Retry
    retry_count: int = 0
    max_retries: int = 2

    # Rollback
    rollback_points: list[CheckpointData] = field(default_factory=list)

    # Cancellation
    cancelled: bool = False
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    # Checkpoints
    checkpoints: list[CheckpointData] = field(default_factory=list)

    # Timeline (engine_id → duration_ms)
    timeline: dict[str, float] = field(default_factory=dict)

    # Event history
    event_log: list[dict[str, Any]] = field(default_factory=list)

    @property
    def elapsed_ms(self) -> float:
        if self.started_at == 0.0:
            return 0.0
        end = self.completed_at if self.completed_at > 0 else time.time()
        return (end - self.started_at) * 1000

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def start(self) -> None:
        """Mark execution as started."""
        self.state = ExecutionState.RUNNING
        self.started_at = time.time()

    def complete(self) -> None:
        """Mark execution as completed."""
        self.state = ExecutionState.COMPLETED
        self.completed_at = time.time()

    def fail(self) -> None:
        """Mark execution as failed."""
        self.state = ExecutionState.FAILED
        self.completed_at = time.time()

    def cancel(self) -> None:
        """Request cancellation."""
        self.cancelled = True
        self.state = ExecutionState.CANCELLED
        self._cancel_event.set()

    def record_engine_time(self, engine_id: str, duration_ms: float) -> None:
        """Record how long an engine took."""
        self.timeline[engine_id] = duration_ms
        self.completed_engines.append(engine_id)

    def add_checkpoint(self, engine_id: str, state: dict[str, Any]) -> None:
        """Save a checkpoint for potential recovery."""
        cp = CheckpointData(
            checkpoint_id=f"cp_{engine_id}_{len(self.checkpoints)}",
            engine_id=engine_id,
            state_snapshot=state,
        )
        self.checkpoints.append(cp)
        self.rollback_points.append(cp)

    def log_event(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Append to the execution event log."""
        self.event_log.append(
            {
                "event": event,
                "timestamp": time.time(),
                "data": data or {},
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "state": self.state.value,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "completed_engines": self.completed_engines,
            "current_engine": self.current_engine,
            "retry_count": self.retry_count,
            "cancelled": self.cancelled,
            "timeline": {k: round(v, 2) for k, v in self.timeline.items()},
            "checkpoints": len(self.checkpoints),
        }
