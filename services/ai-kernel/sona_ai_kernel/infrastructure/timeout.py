"""Timeout management for LLM calls.

Provides a generic timeout wrapper that converts asyncio.TimeoutError
into a domain-meaningful TimeoutError for proper error handling.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any

import structlog

logger = structlog.get_logger()


async def with_timeout[T](
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float,
) -> T:
    """Wrap a coroutine with a timeout.

    Args:
        coro: The coroutine to execute with a timeout.
        timeout_seconds: Maximum time to wait in seconds.

    Returns:
        The result of the coroutine on success.

    Raises:
        TimeoutError: If the operation exceeds the timeout.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except TimeoutError:
        logger.error(
            "operation_timed_out",
            timeout_seconds=timeout_seconds,
        )
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s") from None
