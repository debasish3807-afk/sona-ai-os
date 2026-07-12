"""Interrupt Handler — manages interrupt requests and emergency stops."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class InterruptType(str, Enum):
    """Types of interrupts that can be raised."""

    USER_STOP = "user_stop"
    KERNEL_STOP = "kernel_stop"
    EMERGENCY_STOP = "emergency_stop"
    CANCELLATION = "cancellation"
    GRACEFUL = "graceful"
    FORCED = "forced"
    TIMEOUT_KILL = "timeout_kill"


@dataclass
class InterruptRequest:
    """A request to interrupt a running process or the kernel."""

    interrupt_type: InterruptType
    interrupt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_process: str = ""
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class InterruptHandler:
    """Handles interrupt requests with priority processing.

    Manages pending and historical interrupts, supports cancellation,
    and detects emergency situations.
    """

    def __init__(self) -> None:
        self._pending: list[InterruptRequest] = []
        self._history: list[InterruptRequest] = []

    def request_interrupt(
        self,
        interrupt_type: InterruptType,
        target: str = "",
        reason: str = "",
    ) -> InterruptRequest:
        """Submit an interrupt request."""
        request = InterruptRequest(
            interrupt_type=interrupt_type,
            target_process=target,
            reason=reason,
        )
        self._pending.append(request)
        logger.info(
            "interrupt_requested",
            interrupt_id=request.interrupt_id,
            interrupt_type=interrupt_type.value,
            target=target,
        )
        return request

    def process_pending(self) -> list[InterruptRequest]:
        """Process and return all pending interrupts, moving them to history."""
        processed = list(self._pending)
        self._history.extend(processed)
        self._pending.clear()
        return processed

    def cancel_interrupt(self, interrupt_id: str) -> bool:
        """Cancel a pending interrupt. Returns True if found and cancelled."""
        for i, req in enumerate(self._pending):
            if req.interrupt_id == interrupt_id:
                self._pending.pop(i)
                logger.info("interrupt_cancelled", interrupt_id=interrupt_id)
                return True
        return False

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent interrupt history as dicts."""
        entries = self._history[-limit:]
        return [
            {
                "interrupt_id": r.interrupt_id,
                "interrupt_type": r.interrupt_type.value,
                "target_process": r.target_process,
                "reason": r.reason,
                "timestamp": r.timestamp,
            }
            for r in entries
        ]

    def is_emergency(self) -> bool:
        """Check if any pending interrupt is an emergency."""
        return any(
            req.interrupt_type in (InterruptType.EMERGENCY_STOP, InterruptType.FORCED)
            for req in self._pending
        )
