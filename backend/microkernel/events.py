"""Microkernel events — event types and event data for the kernel event bus."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MicrokernelEventType(str, Enum):
    """All event types emitted by the microkernel."""

    KERNEL_STARTED = "kernel_started"
    KERNEL_STOPPED = "kernel_stopped"
    WORKER_REGISTERED = "worker_registered"
    WORKER_REMOVED = "worker_removed"
    IPC_MESSAGE_SENT = "ipc_message_sent"
    IPC_MESSAGE_RECEIVED = "ipc_message_received"
    SANDBOX_CREATED = "sandbox_created"
    SANDBOX_DESTROYED = "sandbox_destroyed"
    PROCESS_STARTED = "process_started"
    PROCESS_STOPPED = "process_stopped"
    INTERRUPT_TRIGGERED = "interrupt_triggered"
    SCHEDULER_UPDATED = "scheduler_updated"
    RESOURCE_EXCEEDED = "resource_exceeded"
    SECURITY_VIOLATION = "security_violation"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"


@dataclass
class MicrokernelEvent:
    """A single event emitted by the microkernel runtime."""

    event_type: MicrokernelEventType
    source: str
    data: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
        }
