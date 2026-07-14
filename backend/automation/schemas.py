"""Automation schemas and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerType(str, Enum):
    TIME = "time"
    FILE_CHANGE = "file_change"
    FOLDER_CHANGE = "folder_change"
    VOICE_COMMAND = "voice_command"
    API_REQUEST = "api_request"
    MANUAL = "manual"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"


class ActionType(str, Enum):
    AI_CHAT = "ai_chat"
    DEEP_RESEARCH = "deep_research"
    OCR = "ocr"
    MEMORY_STORE = "memory_store"
    FILE_CREATE = "file_create"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    TERMINAL = "terminal"
    GITHUB = "github"
    HTTP_REQUEST = "http_request"
    NOTIFICATION = "notification"


class WorkflowStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"


@dataclass
class Trigger:
    trigger_type: TriggerType
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionStep:
    action_type: ActionType
    params: dict[str, Any] = field(default_factory=dict)
    retry: int = 0
    timeout_seconds: float = 30.0


@dataclass
class Condition:
    field: str = ""
    operator: str = "eq"
    value: Any = None


@dataclass
class WorkflowStep:
    step_type: StepType = StepType.ACTION
    action: ActionStep | None = None
    condition: Condition | None = None
    on_true: list[WorkflowStep] | None = None
    on_false: list[WorkflowStep] | None = None
    steps: list[WorkflowStep] | None = None
    wait_seconds: float = 0.0


@dataclass
class Workflow:
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    trigger: Trigger | None = None
    steps: list[WorkflowStep] = field(default_factory=list)
    enabled: bool = True
    created_at: str = ""


@dataclass
class WorkflowRun:
    run_id: str = ""
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.IDLE
    started_at: str = ""
    completed_at: str = ""
    steps_completed: int = 0
    steps_total: int = 0
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
