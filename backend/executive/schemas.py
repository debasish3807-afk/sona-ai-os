"""Executive Intelligence layer — data models and schemas."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class GoalPriority(str, Enum):
    """Priority levels for goals."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


class GoalState(str, Enum):
    """Lifecycle states for goals."""

    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    MERGED = "merged"


class StrategyType(str, Enum):
    """Strategy optimization targets."""

    FASTEST = "fastest"
    LOWEST_COST = "lowest_cost"
    HIGHEST_QUALITY = "highest_quality"
    SAFEST = "safest"
    BALANCED = "balanced"
    HIGHEST_CONFIDENCE = "highest_confidence"


class ApprovalStatus(str, Enum):
    """Approval gate statuses."""

    AUTO_APPROVED = "auto_approved"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


@dataclass
class Goal:
    """A user or system goal to be achieved."""

    title: str
    description: str
    priority: GoalPriority = GoalPriority.MEDIUM
    state: GoalState = GoalState.CREATED
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    sub_goals: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    deadline: float | None = None
    progress: float = 0.0
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize goal to dictionary."""
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "state": self.state.value,
            "parent_id": self.parent_id,
            "sub_goals": self.sub_goals,
            "dependencies": self.dependencies,
            "success_criteria": self.success_criteria,
            "deadline": self.deadline,
            "progress": self.progress,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Strategy:
    """An execution strategy for achieving a goal."""

    strategy_type: StrategyType
    description: str
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    estimated_confidence: float = 0.5
    risk_level: float = 0.5
    steps: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)
    reasoning: str = ""
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Serialize strategy to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type.value,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_confidence": self.estimated_confidence,
            "risk_level": self.risk_level,
            "steps": self.steps,
            "trade_offs": self.trade_offs,
            "reasoning": self.reasoning,
        }


@dataclass
class Decision:
    """A decision made by the decision engine."""

    alternatives: list[Strategy] = field(default_factory=list)
    selected: Strategy | None = None
    reasoning: str = ""
    confidence: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    latency_ms: float = 0.0
    trace: list[str] = field(default_factory=list)
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize decision to dictionary."""
        return {
            "decision_id": self.decision_id,
            "alternatives": [s.to_dict() for s in self.alternatives],
            "selected": self.selected.to_dict() if self.selected else None,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "risk": self.risk,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "trace": self.trace,
            "created_at": self.created_at,
        }


@dataclass
class ExecutionPlan:
    """An execution plan derived from a decision."""

    goal_id: str
    strategy_id: str
    tasks: list[str] = field(default_factory=list)
    execution_mode: str = "sequential"
    estimated_duration_ms: float = 0.0
    checkpoints: list[str] = field(default_factory=list)
    rollback_path: list[str] = field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Serialize execution plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "strategy_id": self.strategy_id,
            "tasks": self.tasks,
            "execution_mode": self.execution_mode,
            "estimated_duration_ms": self.estimated_duration_ms,
            "checkpoints": self.checkpoints,
            "rollback_path": self.rollback_path,
            "approval_status": self.approval_status.value,
        }
