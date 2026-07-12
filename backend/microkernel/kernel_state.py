"""Kernel State — manages lifecycle transitions for the microkernel."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from microkernel.schemas import KernelStatus

logger = get_logger(__name__)


# Valid state transitions map
VALID_TRANSITIONS: dict[KernelStatus, set[KernelStatus]] = {
    KernelStatus.STOPPED: {KernelStatus.STARTING},
    KernelStatus.STARTING: {KernelStatus.READY, KernelStatus.ERROR},
    KernelStatus.READY: {KernelStatus.RUNNING, KernelStatus.SHUTTING_DOWN, KernelStatus.ERROR},
    KernelStatus.RUNNING: {KernelStatus.PAUSED, KernelStatus.SHUTTING_DOWN, KernelStatus.ERROR},
    KernelStatus.PAUSED: {KernelStatus.RUNNING, KernelStatus.SHUTTING_DOWN, KernelStatus.ERROR},
    KernelStatus.SHUTTING_DOWN: {KernelStatus.STOPPED, KernelStatus.ERROR},
    KernelStatus.ERROR: {KernelStatus.STARTING, KernelStatus.STOPPED},
}


class MicrokernelState:
    """Tracks the lifecycle state of the microkernel with validated transitions."""

    def __init__(self) -> None:
        self._status: KernelStatus = KernelStatus.STOPPED
        self._started_at: float = 0.0
        self._services_count: int = 0
        self._processes_count: int = 0
        self._messages_processed: int = 0

    @property
    def status(self) -> KernelStatus:
        """Current kernel status."""
        return self._status

    def transition(self, target: KernelStatus) -> bool:
        """Attempt a state transition. Returns True if valid and applied."""
        allowed = VALID_TRANSITIONS.get(self._status, set())
        if target not in allowed:
            logger.warning(
                "invalid_state_transition",
                current=self._status.value,
                target=target.value,
            )
            return False

        previous = self._status
        self._status = target

        if target == KernelStatus.STARTING:
            self._started_at = time.time()

        logger.info(
            "kernel_state_transition",
            previous=previous.value,
            current=target.value,
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize current state."""
        return {
            "status": self._status.value,
            "started_at": self._started_at,
            "services_count": self._services_count,
            "processes_count": self._processes_count,
            "messages_processed": self._messages_processed,
        }
