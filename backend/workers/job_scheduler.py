"""Job scheduling with delay and recurring support."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from config.logging import get_logger
from workers.job_queue import JobQueue
from workers.schemas import Job, JobPriority, JobState

logger = get_logger(__name__)


@dataclass
class RecurringJob:
    """Tracks a recurring job schedule."""

    schedule_id: str
    name: str
    handler: str
    interval_seconds: float
    params: dict = field(default_factory=dict)
    active: bool = True


class JobScheduler:
    """Schedules jobs with optional delay and recurring support."""

    def __init__(self, queue: JobQueue) -> None:
        self._queue = queue
        self._scheduled: dict[str, Job] = {}
        self._recurring: dict[str, RecurringJob] = {}
        self._lock = threading.Lock()

    def schedule(
        self,
        name: str,
        handler: str,
        params: dict | None = None,
        priority: JobPriority = JobPriority.NORMAL,
        delay_seconds: float = 0,
    ) -> Job:
        """Schedule a new job, optionally with a delay."""
        scheduled_at = None
        if delay_seconds > 0:
            scheduled_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)

        job = Job(
            name=name,
            handler=handler,
            params=params or {},
            priority=priority,
            scheduled_at=scheduled_at,
        )

        with self._lock:
            self._scheduled[job.job_id] = job

        if delay_seconds <= 0:
            self._queue.enqueue(job)
        else:
            logger.info(
                "job_scheduled_delayed",
                job_id=job.job_id,
                delay=delay_seconds,
            )
        return job

    def schedule_recurring(
        self,
        name: str,
        handler: str,
        interval_seconds: float,
        params: dict | None = None,
    ) -> str:
        """Register a recurring job. Returns schedule_id."""
        schedule_id = str(uuid4())
        recurring = RecurringJob(
            schedule_id=schedule_id,
            name=name,
            handler=handler,
            interval_seconds=interval_seconds,
            params=params or {},
        )
        with self._lock:
            self._recurring[schedule_id] = recurring
        logger.info(
            "recurring_job_registered",
            schedule_id=schedule_id,
            name=name,
            interval=interval_seconds,
        )
        return schedule_id

    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled job by ID."""
        with self._lock:
            job = self._scheduled.get(job_id)
            if job and job.state in (JobState.PENDING, JobState.QUEUED):
                job.state = JobState.CANCELLED
                logger.info("job_cancelled", job_id=job_id)
                return True
            # Check recurring
            if job_id in self._recurring:
                self._recurring[job_id].active = False
                logger.info("recurring_job_cancelled", schedule_id=job_id)
                return True
        return False

    def list_scheduled(self) -> list[Job]:
        """List all tracked scheduled jobs."""
        with self._lock:
            return list(self._scheduled.values())

    def get_stats(self) -> dict:
        """Return scheduler statistics."""
        with self._lock:
            return {
                "total_scheduled": len(self._scheduled),
                "recurring_count": len(self._recurring),
                "active_recurring": sum(1 for r in self._recurring.values() if r.active),
            }
