"""Shared type definitions for the orchestration system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    step_id: str = ""
    description: str = ""
    agent_type: str = ""
    tool: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    priority: int = 50
    status: PlanStatus = PlanStatus.PENDING


@dataclass
class Plan:
    plan_id: str = ""
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    created_at: float = 0.0
    owner: str = ""


@dataclass
class ExecutableTask:
    task_id: str = ""
    agent_type: str = ""
    tool: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 50


@dataclass
class ToolDefinition:
    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    required_capability: str = ""
    dangerous: bool = False


@dataclass
class AgentSpec:
    agent_type: str = ""
    count: int = 1
    capabilities: list[str] = field(default_factory=list)


@dataclass
class Goal:
    goal_id: str = ""
    title: str = ""
    description: str = ""
    status: GoalStatus = GoalStatus.ACTIVE
    progress: float = 0.0
    created_at: float = 0.0
    plan_id: str = ""


@dataclass
class WorkflowStep:
    name: str = ""
    step_type: str = "action"
    status: WorkflowStatus = WorkflowStatus.IDLE
    actions: list[dict[str, Any]] = field(default_factory=list)
    condition: str = ""
    loop_count: int = 1
    depends_on: list[str] = field(default_factory=list)
    on_failure: str = "fail"


@dataclass
class WorkflowDefinition:
    workflow_id: str = ""
    name: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.IDLE
    error: str = ""
