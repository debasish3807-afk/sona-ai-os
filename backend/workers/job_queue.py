"""Priority-based job queue for background execution."""

from __future__ import annotations

import heapq
import threading
from collections import deque

from config.logging import get_logger
from workers.schemas import Job, JobState

logger = get_logger(__name__)


class JobQueue:
    """Thread-safe priority job queue with dead-letter support."""

    def __init__(self, max_size: int = 10000) -> None:
        self._max_size = max_size
        self._heap: list[tuple[int, float, Job]] = []
        self._dead_letters: deque[Job] = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._counter = 0
        self._enqueued_total = 0
        self._dequeued_total = 0

    def enqueue(self, job: Job) -> str:
        """Add a job to the queue. Returns job_id."""
        with self._lock:
            if len(self._heap) >= self._max_size:
                raise RuntimeError("Job queue is full")
            job.state = JobState.QUEUED
            self._counter += 1
            heapq.heappush(self._heap, (job.priority.value, self._counter, job))
            self._enqueued_total += 1
            logger.info("job_enqueued", job_id=job.job_id, name=job.name)
        return job.job_id

    def dequeue(self) -> Job | None:
        """Remove and return the highest-priority job, or None."""
        with self._lock:
            if not self._heap:
                return None
            _, _, job = heapq.heappop(self._heap)
            self._dequeued_total += 1
            return job

    def peek(self) -> Job | None:
        """Return the highest-priority job without removing it."""
        with self._lock:
            if not self._heap:
                return None
            _, _, job = self._heap[0]
            return job

    def dead_letter(self, job: Job) -> None:
        """Move a failed job to the dead-letter queue."""
        with self._lock:
            job.state = JobState.DEAD_LETTER
            self._dead_letters.append(job)
            logger.warning("job_dead_lettered", job_id=job.job_id)

    def get_dead_letters(self, limit: int = 50) -> list[Job]:
        """Retrieve dead-lettered jobs."""
        with self._lock:
            items = list(self._dead_letters)
            return items[:limit]

    @property
    def size(self) -> int:
        """Current number of jobs in the queue."""
        with self._lock:
            return len(self._heap)

    def get_stats(self) -> dict:
        """Return queue statistics."""
        with self._lock:
            return {
                "current_size": len(self._heap),
                "max_size": self._max_size,
                "enqueued_total": self._enqueued_total,
                "dequeued_total": self._dequeued_total,
                "dead_letter_count": len(self._dead_letters),
            }
