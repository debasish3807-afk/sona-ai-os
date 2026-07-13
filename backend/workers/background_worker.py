"""Background worker for processing jobs from the queue."""

from __future__ import annotations

import asyncio
import importlib
from datetime import UTC, datetime
from uuid import uuid4

from config.logging import get_logger
from workers.job_queue import JobQueue
from workers.schemas import Job, JobState

logger = get_logger(__name__)


class BackgroundWorker:
    """Processes jobs from a job queue asynchronously."""

    def __init__(self, queue: JobQueue, worker_id: str | None = None) -> None:
        self._queue = queue
        self._worker_id = worker_id or str(uuid4())[:8]
        self._current_job: Job | None = None
        self._jobs_processed = 0
        self._jobs_failed = 0

    async def process_next(self) -> Job | None:
        """Dequeue and execute the next job. Returns completed job or None."""
        job = self._queue.dequeue()
        if job is None:
            return None
        return await self.execute_job(job)

    async def execute_job(self, job: Job) -> Job:
        """Execute a single job and update its state."""
        self._current_job = job
        job.state = JobState.RUNNING
        logger.info(
            "job_started",
            worker_id=self._worker_id,
            job_id=job.job_id,
            name=job.name,
        )
        try:
            handler_fn = self._resolve_handler(job.handler)
            if asyncio.iscoroutinefunction(handler_fn):
                await handler_fn(**job.params)
            else:
                await asyncio.to_thread(handler_fn, **job.params)
            job.state = JobState.COMPLETED
            job.completed_at = datetime.now(UTC)
            self._jobs_processed += 1
            logger.info("job_completed", job_id=job.job_id)
        except Exception as exc:
            job.state = JobState.FAILED
            job.error = str(exc)
            self._jobs_failed += 1
            logger.error("job_failed", job_id=job.job_id, error=str(exc))
        finally:
            self._current_job = None
        return job

    @property
    def is_idle(self) -> bool:
        """Whether the worker is currently idle."""
        return self._current_job is None

    def get_stats(self) -> dict:
        """Return worker statistics."""
        return {
            "worker_id": self._worker_id,
            "is_idle": self.is_idle,
            "jobs_processed": self._jobs_processed,
            "jobs_failed": self._jobs_failed,
            "current_job": (self._current_job.job_id if self._current_job else None),
        }

    @staticmethod
    def _resolve_handler(handler: str):
        """Resolve a dotted handler path to a callable."""
        module_path, _, func_name = handler.rpartition(".")
        if not module_path:
            raise ValueError(f"Invalid handler path: {handler}")
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
