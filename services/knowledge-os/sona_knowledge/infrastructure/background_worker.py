"""Background worker for asynchronous document processing.

Provides a queue-based system for processing documents asynchronously
with configurable concurrency and progress tracking.
"""

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger()


class TaskStatus(StrEnum):
    """Status of a background task."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    """A task to be processed in the background."""

    task_id: str
    payload: dict[str, Any]
    status: TaskStatus = TaskStatus.QUEUED
    result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BackgroundWorker:
    """Async background worker for document processing.

    Features:
    - Queue-based document processing
    - Async processing with configurable concurrency
    - Progress tracking (queued, processing, completed, failed)
    """

    def __init__(self, max_concurrency: int = 3) -> None:
        """Initialize the background worker.

        Args:
            max_concurrency: Maximum number of concurrent tasks.
        """
        self._max_concurrency = max_concurrency
        self._queue: asyncio.Queue[BackgroundTask] = asyncio.Queue()
        self._tasks: dict[str, BackgroundTask] = {}
        self._running = False
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._processor: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]] | None = None

    @property
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._running

    @property
    def queue_size(self) -> int:
        """Get current number of queued tasks."""
        return self._queue.qsize()

    @property
    def task_count(self) -> int:
        """Get total number of tracked tasks."""
        return len(self._tasks)

    def set_processor(
        self, processor: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]
    ) -> None:
        """Set the async processing function.

        Args:
            processor: Async function that processes task payloads.
        """
        self._processor = processor

    async def submit(self, task_id: str, payload: dict[str, Any]) -> BackgroundTask:
        """Submit a task for background processing.

        Args:
            task_id: Unique identifier for the task.
            payload: Data to be processed.

        Returns:
            The created BackgroundTask.
        """
        task = BackgroundTask(task_id=task_id, payload=payload)
        self._tasks[task_id] = task
        await self._queue.put(task)
        logger.info("task_submitted", task_id=task_id)
        return task

    def get_status(self, task_id: str) -> TaskStatus | None:
        """Get the status of a submitted task.

        Args:
            task_id: The task identifier.

        Returns:
            TaskStatus or None if task not found.
        """
        task = self._tasks.get(task_id)
        return task.status if task else None

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """Get the full task details.

        Args:
            task_id: The task identifier.

        Returns:
            BackgroundTask or None if not found.
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[BackgroundTask]:
        """Get all tracked tasks.

        Returns:
            List of all BackgroundTask instances.
        """
        return list(self._tasks.values())

    async def process_one(self) -> BackgroundTask | None:
        """Process a single task from the queue.

        Returns:
            The processed BackgroundTask, or None if queue is empty.
        """
        if self._queue.empty():
            return None

        task = await self._queue.get()
        await self._execute_task(task)
        return task

    async def process_all(self) -> list[BackgroundTask]:
        """Process all queued tasks respecting concurrency limits.

        Returns:
            List of processed BackgroundTask instances.
        """
        self._running = True
        processed: list[BackgroundTask] = []

        tasks_to_process: list[BackgroundTask] = []
        while not self._queue.empty():
            tasks_to_process.append(await self._queue.get())

        async def process_with_semaphore(task: BackgroundTask) -> None:
            async with self._semaphore:
                await self._execute_task(task)
                processed.append(task)

        await asyncio.gather(*(process_with_semaphore(t) for t in tasks_to_process))
        self._running = False
        return processed

    async def _execute_task(self, task: BackgroundTask) -> None:
        """Execute a single task.

        Args:
            task: The task to execute.
        """
        task.status = TaskStatus.PROCESSING
        logger.info("task_processing", task_id=task.task_id)

        try:
            if self._processor is None:
                raise RuntimeError("No processor set")
            result = await self._processor(task.payload)
            task.result = result
            task.status = TaskStatus.COMPLETED
            logger.info("task_completed", task_id=task.task_id)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error("task_failed", task_id=task.task_id, error=str(e))
