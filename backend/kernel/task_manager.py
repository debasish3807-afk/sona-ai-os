"""Task management for kernel operations.

Manages the lifecycle of tasks submitted to the AI kernel including
creation, queuing, execution tracking, and completion handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    """Execution status of a task."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(int, Enum):
    """Task execution priority."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    BACKGROUND = 100


class TaskType(str, Enum):
    """Classification of task types."""

    CHAT = "chat"
    COMPLETION = "completion"
    ANALYSIS = "analysis"
    CODE_GENERATION = "code_generation"
    SEARCH = "search"
    AUTOMATION = "automation"
    TOOL_CALL = "tool_call"
    MULTI_STEP = "multi_step"


@dataclass
class TaskConfig:
    """Configuration for task execution.

    Attributes:
        max_retries: Maximum retry attempts on failure.
        timeout_seconds: Maximum execution time.
        model_preference: Preferred model for execution.
        streaming: Whether to stream the response.
        temperature: Model temperature parameter.
        max_tokens: Maximum response tokens.
        metadata: Additional task configuration.
    """

    max_retries: int = 2
    timeout_seconds: int = 120
    model_preference: str | None = None
    streaming: bool = False
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Represents a unit of work submitted to the kernel.

    Attributes:
        task_id: Unique task identifier.
        session_id: Associated session identifier.
        task_type: Classification of the task.
        input_data: Task input payload.
        config: Execution configuration.
        status: Current task status.
        priority: Execution priority.
        result: Task result (populated on completion).
        error: Error details (populated on failure).
        created_at: Task creation timestamp.
        started_at: Execution start timestamp.
        completed_at: Completion timestamp.
        attempts: Number of execution attempts.
        metadata: Additional task metadata.
    """

    session_id: str
    task_type: TaskType
    input_data: dict[str, Any]
    task_id: str = field(default_factory=lambda: str(uuid4()))
    config: TaskConfig = field(default_factory=TaskConfig)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )

    @property
    def duration_ms(self) -> float | None:
        """Calculate task execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None


@dataclass
class TaskSummary:
    """Lightweight task summary for listing and monitoring.

    Attributes:
        task_id: Task identifier.
        session_id: Associated session.
        task_type: Task classification.
        status: Current status.
        priority: Task priority.
        created_at: Creation timestamp.
        duration_ms: Execution duration (if completed).
    """

    task_id: str
    session_id: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    duration_ms: float | None = None


class TaskManager(ABC):
    """Abstract interface for task management.

    Handles the full lifecycle of tasks from creation through
    execution and completion.
    """

    @abstractmethod
    async def create_task(
        self,
        session_id: str,
        task_type: TaskType,
        input_data: dict[str, Any],
        config: TaskConfig | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Task:
        """Create a new task for execution.

        Args:
            session_id: Associated session.
            task_type: Type classification for the task.
            input_data: Task input payload.
            config: Optional execution configuration.
            priority: Task priority level.

        Returns:
            Newly created Task instance.
        """
        ...

    @abstractmethod
    async def get_task(self, task_id: str) -> Task | None:
        """Retrieve a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            Task instance or None if not found.
        """
        ...

    @abstractmethod
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> Task | None:
        """Update the status of a task.

        Args:
            task_id: The task to update.
            status: New task status.
            result: Optional result data (for completed tasks).
            error: Optional error details (for failed tasks).

        Returns:
            Updated Task or None if not found.
        """
        ...

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task.

        Args:
            task_id: The task to cancel.

        Returns:
            True if the task was successfully cancelled.
        """
        ...

    @abstractmethod
    async def list_tasks(
        self,
        session_id: str | None = None,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TaskSummary]:
        """List tasks with optional filtering.

        Args:
            session_id: Optional filter by session.
            status: Optional filter by status.
            task_type: Optional filter by type.
            limit: Maximum tasks to return.
            offset: Number of tasks to skip.

        Returns:
            List of TaskSummary instances.
        """
        ...

    @abstractmethod
    async def retry_task(self, task_id: str) -> Task | None:
        """Retry a failed task.

        Creates a new execution attempt for a previously
        failed task, respecting max_retries configuration.

        Args:
            task_id: The task to retry.

        Returns:
            Updated Task with incremented attempts, or None.

        Raises:
            ValueError: If max retries exceeded.
        """
        ...

    @abstractmethod
    async def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Clean up stale tasks that have exceeded their timeout.

        Args:
            max_age_seconds: Maximum age for pending tasks.

        Returns:
            Number of tasks cleaned up.
        """
        ...
