"""Async request queue with priority and backpressure."""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class QueuedRequest:
    """A request waiting in the queue.

    Attributes:
        id: Unique identifier for the queued request.
        priority: Priority level (1=highest, 10=lowest).
        request: The request payload.
        future: Future that resolves when the request is processed.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 5
    request: Any = None
    future: asyncio.Future[Any] | None = field(default=None, repr=False)

    def __lt__(self, other: object) -> bool:
        """Compare by priority for priority queue ordering."""
        if not isinstance(other, QueuedRequest):
            return NotImplemented
        return self.priority < other.priority


class RequestQueue:
    """Priority queue for managing concurrent inference requests.

    Provides backpressure through a maximum queue size and limits
    concurrent processing through a semaphore.
    """

    def __init__(self, max_size: int = 100, max_concurrent: int = 10) -> None:
        """Initialize the request queue.

        Args:
            max_size: Maximum number of requests that can be queued.
            max_concurrent: Maximum concurrent requests being processed.
        """
        self._queue: asyncio.PriorityQueue[tuple[int, str, QueuedRequest]] = asyncio.PriorityQueue(
            maxsize=max_size
        )
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_size = max_size
        self._active = 0
        self._total_processed = 0

    async def enqueue(self, request: Any, priority: int = 5) -> asyncio.Future[Any]:
        """Add request to queue, returns future for result.

        Args:
            request: The request payload to queue.
            priority: Priority level (1=highest, 10=lowest).

        Returns:
            A future that resolves when the request is processed.

        Raises:
            asyncio.QueueFull: If the queue is at maximum capacity.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        queued = QueuedRequest(
            priority=priority,
            request=request,
            future=future,
        )
        # Use priority and id for ordering tuple
        self._queue.put_nowait((priority, queued.id, queued))
        logger.debug(
            "request_enqueued",
            request_id=queued.id,
            priority=priority,
            queue_size=self._queue.qsize(),
        )
        return future

    async def dequeue(self) -> QueuedRequest:
        """Remove and return the highest priority request.

        Returns:
            The highest priority queued request.
        """
        await self._semaphore.acquire()
        _, _, queued = await self._queue.get()
        self._active += 1
        return queued

    def mark_done(self, queued: QueuedRequest, result: Any = None) -> None:
        """Mark a request as completed and resolve its future.

        Args:
            queued: The queued request that was processed.
            result: The result to set on the future.
        """
        self._active -= 1
        self._total_processed += 1
        self._semaphore.release()
        if queued.future and not queued.future.done():
            queued.future.set_result(result)
        self._queue.task_done()
        logger.debug(
            "request_completed",
            request_id=queued.id,
            active=self._active,
            total_processed=self._total_processed,
        )

    def mark_failed(self, queued: QueuedRequest, error: Exception) -> None:
        """Mark a request as failed and set its future exception.

        Args:
            queued: The queued request that failed.
            error: The exception that caused the failure.
        """
        self._active -= 1
        self._semaphore.release()
        if queued.future and not queued.future.done():
            queued.future.set_exception(error)
        self._queue.task_done()
        logger.warning(
            "request_failed",
            request_id=queued.id,
            error=str(error),
        )

    @property
    def size(self) -> int:
        """Return the current number of queued requests."""
        return self._queue.qsize()

    @property
    def active(self) -> int:
        """Return the number of currently processing requests."""
        return self._active

    @property
    def total_processed(self) -> int:
        """Return the total number of requests processed."""
        return self._total_processed
