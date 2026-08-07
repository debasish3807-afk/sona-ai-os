"""Retry logic with exponential backoff and jitter.

Provides a generic retry wrapper for async operations that implements
exponential backoff with optional jitter to prevent thundering herds.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable

import structlog

logger = structlog.get_logger()


class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter: Whether to add random jitter to delays.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = True,
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts.
            base_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay cap in seconds.
            jitter: Whether to add random jitter to delays.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter


async def with_retry[T](
    fn: Callable[..., Awaitable[T]],
    config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Execute an async function with exponential backoff retry.

    Retries the provided async callable on failure, using exponential
    backoff with optional jitter. Only retries on exceptions matching
    the retryable_exceptions tuple.

    Args:
        fn: Async callable to execute (takes no arguments).
        config: Retry configuration. Uses defaults if None.
        retryable_exceptions: Tuple of exception types that trigger retry.

    Returns:
        The return value of fn on success.

    Raises:
        The last exception raised by fn if all retries are exhausted.
    """
    if config is None:
        config = RetryConfig()

    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as exc:
            last_exception = exc
            if attempt >= config.max_retries:
                logger.error(
                    "retry_exhausted",
                    attempts=attempt + 1,
                    error=str(exc),
                )
                raise

            delay = min(config.base_delay * (2**attempt), config.max_delay)
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)  # noqa: S311

            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=config.max_retries,
                delay_seconds=round(delay, 3),
                error=str(exc),
            )
            await asyncio.sleep(delay)

    # This should never be reached, but satisfies type checker
    assert last_exception is not None
    raise last_exception
