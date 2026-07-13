"""Retry policies for failed jobs."""

from __future__ import annotations

from dataclasses import dataclass

from config.logging import get_logger
from workers.schemas import Job, JobState

logger = get_logger(__name__)


@dataclass
class RetryPolicy:
    """Configuration for job retry behavior."""

    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 60.0
    backoff_factor: float = 2.0


class RetryManager:
    """Manages retry logic for failed jobs."""

    def __init__(self, default_policy: RetryPolicy | None = None) -> None:
        self._default_policy = default_policy or RetryPolicy()
        self._policies: dict[str, RetryPolicy] = {}

    def set_policy(self, handler: str, policy: RetryPolicy) -> None:
        """Set a custom retry policy for a specific handler."""
        self._policies[handler] = policy

    def should_retry(self, job: Job) -> bool:
        """Determine if a job should be retried."""
        policy = self._policies.get(job.handler, self._default_policy)
        return job.state == JobState.FAILED and job.retry_count < policy.max_retries

    def get_delay(self, job: Job) -> float:
        """Calculate backoff delay for the next retry attempt."""
        policy = self._policies.get(job.handler, self._default_policy)
        delay = policy.backoff_base * (policy.backoff_factor**job.retry_count)
        return min(delay, policy.backoff_max)

    def record_failure(self, job: Job, error: str) -> Job:
        """Record a failure and prepare job for retry or dead-letter."""
        job.error = error
        job.retry_count += 1
        policy = self._policies.get(job.handler, self._default_policy)

        if job.retry_count >= policy.max_retries:
            job.state = JobState.DEAD_LETTER
            logger.warning(
                "job_max_retries_exceeded",
                job_id=job.job_id,
                retries=job.retry_count,
            )
        else:
            job.state = JobState.PENDING
            logger.info(
                "job_retry_scheduled",
                job_id=job.job_id,
                retry=job.retry_count,
                delay=self.get_delay(job),
            )
        return job
