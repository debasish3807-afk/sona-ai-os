"""Retry manager for Brain OS step execution.

Handles retry logic with exponential backoff for failed steps,
respecting the retryable flag and configurable retry limits.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_thalamus.domain.execution_plan import ExecutionStep

logger = structlog.get_logger()


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts per step.
        base_delay_seconds: Initial delay between retries.
        max_delay_seconds: Maximum delay cap.
        jitter: Whether to add random jitter to delays.
        backoff_factor: Multiplier for exponential backoff.
    """

    max_retries: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    jitter: bool = True
    backoff_factor: float = 2.0


@dataclass
class RetryState:
    """Tracks retry state for a single step.

    Attributes:
        step_id: Identifier of the step being retried.
        attempt_count: Number of attempts made so far.
        errors: List of error messages from each attempt.
        exhausted: Whether all retries have been used.
    """

    step_id: str
    attempt_count: int = 0
    errors: list[str] = field(default_factory=list)
    exhausted: bool = False


class RetryManager:
    """Manages retry logic for failed execution steps.

    Provides exponential backoff with jitter, tracks retry attempts,
    and determines when retries are exhausted.
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        """Initialize retry manager with configuration.

        Args:
            config: Retry configuration. Uses defaults if None.
        """
        self._config = config or RetryConfig()
        self._retry_states: dict[str, RetryState] = {}

    @property
    def config(self) -> RetryConfig:
        """Return the retry configuration."""
        return self._config

    def should_retry(self, step: ExecutionStep, result: StepResult) -> bool:
        """Determine if a failed step should be retried.

        Args:
            step: The step that failed.
            result: The failed step result.

        Returns:
            True if the step should be retried.
        """
        if not step.retryable:
            return False

        if result.state != StepState.FAILED:
            return False

        state = self._get_or_create_state(step.step_id)
        return state.attempt_count < self._config.max_retries

    def record_attempt(self, step_id: str, error: str) -> RetryState:
        """Record a retry attempt for a step.

        Args:
            step_id: Identifier of the step being retried.
            error: Error message from the failed attempt.

        Returns:
            The updated retry state.
        """
        state = self._get_or_create_state(step_id)
        state.attempt_count += 1
        state.errors.append(error)

        if state.attempt_count >= self._config.max_retries:
            state.exhausted = True

        logger.info(
            "retry_attempt_recorded",
            step_id=step_id,
            attempt=state.attempt_count,
            max_retries=self._config.max_retries,
            exhausted=state.exhausted,
        )
        return state

    async def wait_before_retry(self, step_id: str) -> float:
        """Wait the appropriate backoff duration before retrying.

        Args:
            step_id: Identifier of the step to calculate delay for.

        Returns:
            The actual delay waited in seconds.
        """
        state = self._get_or_create_state(step_id)
        delay = self._calculate_delay(state.attempt_count)

        logger.debug(
            "retry_waiting",
            step_id=step_id,
            delay_seconds=round(delay, 3),
            attempt=state.attempt_count,
        )
        await asyncio.sleep(delay)
        return delay

    def get_retry_state(self, step_id: str) -> RetryState | None:
        """Get the current retry state for a step.

        Args:
            step_id: Identifier of the step.

        Returns:
            The RetryState if tracked, None otherwise.
        """
        return self._retry_states.get(step_id)

    def is_exhausted(self, step_id: str) -> bool:
        """Check if retries are exhausted for a step.

        Args:
            step_id: Identifier of the step.

        Returns:
            True if max retries reached.
        """
        state = self._retry_states.get(step_id)
        if state is None:
            return False
        return state.exhausted

    def get_attempt_count(self, step_id: str) -> int:
        """Get the number of attempts for a step.

        Args:
            step_id: Identifier of the step.

        Returns:
            Number of attempts made.
        """
        state = self._retry_states.get(step_id)
        return state.attempt_count if state else 0

    def reset(self, step_id: str) -> None:
        """Reset retry state for a step.

        Args:
            step_id: Identifier of the step to reset.
        """
        if step_id in self._retry_states:
            del self._retry_states[step_id]

    def _get_or_create_state(self, step_id: str) -> RetryState:
        """Get or create retry state for a step.

        Args:
            step_id: Identifier of the step.

        Returns:
            The existing or newly created retry state.
        """
        if step_id not in self._retry_states:
            self._retry_states[step_id] = RetryState(step_id=step_id)
        return self._retry_states[step_id]

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate the backoff delay for a given attempt number.

        Args:
            attempt: The current attempt number (0-indexed).

        Returns:
            Delay in seconds with optional jitter.
        """
        delay = min(
            self._config.base_delay_seconds * (self._config.backoff_factor ** attempt),
            self._config.max_delay_seconds,
        )
        if self._config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)  # noqa: S311
        return delay
