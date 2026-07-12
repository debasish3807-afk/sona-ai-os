"""Worker pool management for task execution."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from runtime.schemas import WorkerInfo, WorkerState, WorkerType, WorkflowTask

logger = get_logger(__name__)


class WorkerPool:
    """Manages a pool of workers for executing workflow tasks."""

    def __init__(self, max_workers: int = 8) -> None:
        self._workers: dict[str, WorkerInfo] = {}
        self._max_workers: int = max_workers

    def create_worker(self, worker_type: WorkerType = WorkerType.CPU) -> WorkerInfo:
        """Create a new worker and add it to the pool."""
        worker = WorkerInfo(worker_type=worker_type)
        self._workers[worker.worker_id] = worker
        logger.debug("worker_created", worker_id=worker.worker_id, type=worker_type.value)
        return worker

    def allocate(self, task: WorkflowTask) -> WorkerInfo | None:
        """Allocate an available worker for a task."""
        available = self.get_available()
        if not available:
            if len(self._workers) < self._max_workers:
                worker = self.create_worker()
            else:
                return None
        else:
            worker = available[0]

        worker.state = WorkerState.ALLOCATED
        worker.current_task = task.task_id
        logger.debug("worker_allocated", worker_id=worker.worker_id, task_id=task.task_id)
        return worker

    def release(self, worker_id: str) -> bool:
        """Release a worker back to the pool."""
        if worker_id not in self._workers:
            return False
        worker = self._workers[worker_id]
        worker.state = WorkerState.CREATED
        worker.current_task = ""
        worker.tasks_completed += 1
        logger.debug("worker_released", worker_id=worker_id)
        return True

    def get_available(self) -> list[WorkerInfo]:
        """Return workers in CREATED state (available for allocation)."""
        return [w for w in self._workers.values() if w.state == WorkerState.CREATED]

    def get_busy(self) -> list[WorkerInfo]:
        """Return workers currently allocated or running."""
        return [
            w
            for w in self._workers.values()
            if w.state in (WorkerState.ALLOCATED, WorkerState.RUNNING)
        ]

    def shutdown_worker(self, worker_id: str) -> bool:
        """Shutdown a specific worker."""
        if worker_id not in self._workers:
            return False
        self._workers[worker_id].state = WorkerState.SHUTDOWN
        logger.info("worker_shutdown", worker_id=worker_id)
        return True

    def drain_all(self) -> int:
        """Drain all workers (mark as draining), return count."""
        count = 0
        for worker in self._workers.values():
            if worker.state not in (WorkerState.SHUTDOWN, WorkerState.DRAINING):
                worker.state = WorkerState.DRAINING
                count += 1
        return count

    def get_utilization(self) -> float:
        """Return pool utilization as a ratio (0-1)."""
        if not self._workers:
            return 0.0
        busy = len(self.get_busy())
        return busy / len(self._workers)

    def resize(self, new_max: int) -> None:
        """Resize the maximum worker pool capacity."""
        self._max_workers = max(1, new_max)
        logger.info("pool_resized", new_max=self._max_workers)

    def get_stats(self) -> dict[str, Any]:
        """Return pool statistics."""
        return {
            "total_workers": len(self._workers),
            "max_workers": self._max_workers,
            "available": len(self.get_available()),
            "busy": len(self.get_busy()),
            "utilization": self.get_utilization(),
        }
