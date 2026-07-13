"""Retry policy with exponential backoff for AI operations."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable, Coroutine
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AIRetryPolicy:
    """Retry policy with exponential backoff and jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry on failure."""
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                if attempt == self._max_retries:
                    break
                delay = self.get_delay(attempt)
                logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    delay=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

        raise last_exception  # type: ignore[misc]

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self._base_delay * (2**attempt)
        delay = min(delay, self._max_delay)
        jitter = random.uniform(0, delay * 0.1)  # noqa: S311
        return float(delay + jitter)
