"""Agent task execution engine.

Manages the actual execution of tasks on agents including
concurrency control, timeout management, retry logic, and
result collection.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from agents.base import BaseAgent
from agents.context import ExecutionContext, ExecutionResult


class ExecutionPriority(int, Enum):
    """Execution priority levels."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    BACKGROUND = 100


class ExecutionStatus(str, Enum):
    """Status of an execution job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class ExecutionJob:
    """A queued execution job.

    Attributes:
        job_id: Unique job identifier.
        agent_id: Target agent.
        context: Execution context.
        priority: Job priority.
        status: Current job status.
        max_retries: Maximum retry attempts.
        current_attempt: Current attempt number.
        timeout_seconds: Maximum execution time.
        result: Final result (when complete).
        metadata: Additional job metadata.
    """

    agent_id: str
    context: ExecutionContext
    job_id: str = field(default_factory=lambda: str(uuid4()))
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    status: ExecutionStatus = ExecutionStatus.QUEUED
    max_retries: int = 2
    current_attempt: int = 0
    timeout_seconds: float = 120.0
    result: ExecutionResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        )

    @property
    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return self.current_attempt < self.max_retries


class AgentExecutor(ABC):
    """Abstract interface for agent task execution.

    Manages concurrent task execution with queue management,
    timeout handling, retry logic, and result collection.
    """

    @abstractmethod
    async def submit(
        self,
        agent: BaseAgent,
        context: ExecutionContext,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        timeout_seconds: float | None = None,
    ) -> ExecutionJob:
        """Submit a task for execution.

        Args:
            agent: The agent to execute the task.
            context: Execution context with task details.
            priority: Execution priority.
            timeout_seconds: Override default timeout.

        Returns:
            ExecutionJob tracking the submission.
        """
        ...

    @abstractmethod
    async def submit_stream(
        self,
        agent: BaseAgent,
        context: ExecutionContext,
    ) -> AsyncIterator[dict[str, Any]]:
        """Submit a task for streaming execution.

        Args:
            agent: The agent to execute.
            context: Execution context.

        Yields:
            Incremental result chunks.
        """
        ...

    @abstractmethod
    async def execute_immediate(
        self,
        agent: BaseAgent,
        context: ExecutionContext,
        timeout_seconds: float | None = None,
    ) -> ExecutionResult:
        """Execute a task immediately (bypassing queue).

        Args:
            agent: The agent to execute.
            context: Execution context.
            timeout_seconds: Maximum execution time.

        Returns:
            ExecutionResult from the agent.

        Raises:
            AgentExecutionError: On failure.
            AgentTimeoutError: On timeout.
        """
        ...

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        """Cancel a queued or running job.

        Args:
            job_id: The job to cancel.

        Returns:
            True if cancelled.
        """
        ...

    @abstractmethod
    async def get_job(self, job_id: str) -> ExecutionJob | None:
        """Get a job by ID.

        Args:
            job_id: The job identifier.

        Returns:
            ExecutionJob or None.
        """
        ...

    @abstractmethod
    async def get_queue_size(self, agent_id: str | None = None) -> int:
        """Get the execution queue size.

        Args:
            agent_id: Optional filter by agent.

        Returns:
            Number of queued jobs.
        """
        ...

    @abstractmethod
    async def get_running_count(self, agent_id: str | None = None) -> int:
        """Get number of currently executing jobs.

        Args:
            agent_id: Optional filter by agent.

        Returns:
            Number of running jobs.
        """
        ...

    @abstractmethod
    async def drain(self, timeout_seconds: float = 30.0) -> int:
        """Wait for all running jobs to complete.

        Args:
            timeout_seconds: Maximum wait time.

        Returns:
            Number of jobs that completed.
        """
        ...
