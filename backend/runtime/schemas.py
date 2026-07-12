"""Core data schemas for the Runtime & Autonomous Workflow Engine."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class WorkflowState(str, Enum):
    """Lifecycle states for a workflow."""

    CREATED = "created"
    READY = "ready"
    QUEUED = "queued"
    WAITING = "waiting"
    RUNNING = "running"
    BLOCKED = "blocked"
    PAUSED = "paused"
    RETRYING = "retrying"
    ROLLING_BACK = "rolling_back"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(str, Enum):
    """Supported workflow execution patterns."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    NESTED = "nested"
    LOOP = "loop"
    PIPELINE = "pipeline"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"
    DYNAMIC = "dynamic"
    EVENT_DRIVEN = "event_driven"
    SCHEDULED = "scheduled"
    STREAMING = "streaming"
    LONG_RUNNING = "long_running"
    HUMAN_APPROVAL = "human_approval"


class TaskState(str, Enum):
    """Lifecycle states for an individual task."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkerType(str, Enum):
    """Types of workers in the execution pool."""

    CPU = "cpu"
    IO = "io"
    GPU = "gpu"
    ASYNC = "async"
    BACKGROUND = "background"
    SANDBOX = "sandbox"
    PLUGIN = "plugin"
    STREAMING = "streaming"


class WorkerState(str, Enum):
    """Lifecycle states for a worker."""

    CREATED = "created"
    ALLOCATED = "allocated"
    RUNNING = "running"
    PAUSED = "paused"
    DRAINING = "draining"
    SHUTDOWN = "shutdown"


class QueuePriority(IntEnum):
    """Priority levels for the task queue (lower = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class WorkflowTask:
    """A single unit of work within a workflow."""

    name: str
    capability_id: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    priority: QueuePriority = QueuePriority.NORMAL
    result: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 60.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "capability_id": self.capability_id,
            "params": self.params,
            "dependencies": self.dependencies,
            "state": self.state.value,
            "priority": int(self.priority),
            "result": self.result,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class Workflow:
    """A complete workflow definition with tasks and metadata."""

    name: str
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    state: WorkflowState = WorkflowState.CREATED
    tasks: list[WorkflowTask] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    checkpoints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "workflow_type": self.workflow_type.value,
            "state": self.state.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "total_duration_ms": self.total_duration_ms,
            "checkpoints": self.checkpoints,
        }


@dataclass
class WorkerInfo:
    """Information about a worker in the execution pool."""

    worker_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    worker_type: WorkerType = WorkerType.CPU
    state: WorkerState = WorkerState.CREATED
    current_task: str = ""
    tasks_completed: int = 0
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize worker info to dictionary."""
        return {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type.value,
            "state": self.state.value,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "started_at": self.started_at,
        }
