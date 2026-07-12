"""Process Supervisor — manages process lifecycle and crash recovery."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from config.logging import get_logger
from microkernel.schemas import ProcessState

logger = get_logger(__name__)


@dataclass
class ProcessInfo:
    """Metadata for a supervised process."""

    name: str
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ProcessState = ProcessState.CREATED
    service_id: str = ""
    started_at: float = field(default_factory=time.time)
    restart_count: int = 0
    max_restarts: int = 3
    backoff_seconds: float = 1.0


class ProcessSupervisor:
    """Supervises processes with lifecycle management and crash recovery.

    Tracks process states, handles restarts with exponential backoff,
    and provides graceful shutdown coordination.
    """

    def __init__(self) -> None:
        self._processes: dict[str, ProcessInfo] = {}

    def spawn(self, name: str, service_id: str = "") -> ProcessInfo:
        """Create and start a new supervised process."""
        process = ProcessInfo(name=name, service_id=service_id)
        process.state = ProcessState.RUNNING
        self._processes[process.process_id] = process
        logger.info("process_spawned", process_id=process.process_id, name=name)
        return process

    def stop(self, process_id: str) -> bool:
        """Stop a running process."""
        process = self._processes.get(process_id)
        if process is None:
            return False

        if process.state not in (ProcessState.RUNNING, ProcessState.PAUSED):
            return False

        process.state = ProcessState.STOPPED
        logger.info("process_stopped", process_id=process_id)
        return True

    def restart(self, process_id: str) -> bool:
        """Restart a process if within restart limits."""
        process = self._processes.get(process_id)
        if process is None:
            return False

        if process.restart_count >= process.max_restarts:
            logger.warning("process_max_restarts", process_id=process_id)
            return False

        process.restart_count += 1
        process.state = ProcessState.RUNNING
        process.started_at = time.time()
        logger.info(
            "process_restarted",
            process_id=process_id,
            restart_count=process.restart_count,
        )
        return True

    def get(self, process_id: str) -> ProcessInfo | None:
        """Retrieve process info by ID."""
        return self._processes.get(process_id)

    def list_all(self) -> list[ProcessInfo]:
        """List all supervised processes."""
        return list(self._processes.values())

    def mark_crashed(self, process_id: str) -> bool:
        """Mark a process as crashed."""
        process = self._processes.get(process_id)
        if process is None:
            return False

        process.state = ProcessState.CRASHED
        logger.warning("process_crashed", process_id=process_id, name=process.name)
        return True

    def recover(self, process_id: str) -> bool:
        """Attempt to recover a crashed process with backoff."""
        process = self._processes.get(process_id)
        if process is None:
            return False

        if process.state != ProcessState.CRASHED:
            return False

        if process.restart_count >= process.max_restarts:
            logger.error("process_unrecoverable", process_id=process_id)
            return False

        process.state = ProcessState.RECOVERING
        process.backoff_seconds = process.backoff_seconds * (2**process.restart_count)
        process.restart_count += 1
        process.state = ProcessState.RUNNING
        process.started_at = time.time()

        logger.info(
            "process_recovered",
            process_id=process_id,
            restart_count=process.restart_count,
            backoff=process.backoff_seconds,
        )
        return True

    def get_crashed(self) -> list[ProcessInfo]:
        """Get all processes in crashed state."""
        return [p for p in self._processes.values() if p.state == ProcessState.CRASHED]

    def graceful_shutdown_all(self) -> int:
        """Stop all running processes gracefully. Returns count stopped."""
        count = 0
        for process in self._processes.values():
            if process.state in (ProcessState.RUNNING, ProcessState.PAUSED):
                process.state = ProcessState.STOPPED
                count += 1
        logger.info("graceful_shutdown_complete", stopped_count=count)
        return count
