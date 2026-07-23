"""Retry & error recovery for automation execution."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class RetryHandler:
    """Configurable retry logic with exponential backoff."""

    def __init__(
        self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0
    ) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._backoff_factor = backoff_factor

    def should_retry(self, attempt: int) -> bool:
        return attempt < self._max_retries

    def delay(self, attempt: int) -> float:
        return self._base_delay * (self._backoff_factor**attempt)

    async def execute_with_retry(
        self, fn: Any, *args: Any, on_retry: Any = None, **kwargs: Any
    ) -> dict[str, Any]:
        last_error = ""
        for attempt in range(self._max_retries + 1):
            try:
                result = await fn(*args, **kwargs)
                return {"success": True, "result": result, "attempts": attempt + 1}
            except (ValueError, TypeError, RuntimeError, OSError, KeyError, StopIteration) as exc:
                last_error = str(exc)
                logger.warning("retry_attempt_failed", attempt=attempt, error=last_error)
                if on_retry:
                    on_retry(attempt, last_error)
                if self.should_retry(attempt + 1):
                    delay = self.delay(attempt)
                    logger.info("retry_scheduling", next_attempt=attempt + 1, delay=delay)
                    await _async_sleep(delay)
        return {"success": False, "error": last_error, "attempts": self._max_retries + 1}


async def _async_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
