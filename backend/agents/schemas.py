"""Agent schemas — pure dataclass definitions for the multi-agent fabric."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Types of agents in the system."""

    PLANNER = "planner"
    RESEARCH = "research"
    MEMORY = "memory"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    CODING = "coding"
    TESTING = "testing"
    SECURITY = "security"
    DEVOPS = "devops"
    DOCUMENTATION = "documentation"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    RECOVERY = "recovery"
    CUSTOM = "custom"


class AgentState(str, Enum):
    """Lifecycle states for an agent."""

    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class CoordinationMode(str, Enum):
    """Coordination strategies for multi-agent execution."""

    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    SUPERVISOR = "supervisor"
    SWARM = "swarm"
    VOTING = "voting"
    CONSENSUS = "consensus"
    DYNAMIC = "dynamic"


class AgentPriority(IntEnum):
    """Priority levels for agents (lower = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Agent:
    """Core agent representation."""

    name: str
    agent_type: AgentType
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: AgentState = AgentState.CREATED
    capabilities: list[str] = field(default_factory=list)
    priority: AgentPriority = AgentPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "state": self.state.value,
            "capabilities": self.capabilities,
            "priority": int(self.priority),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class AgentTask:
    """A task assigned to an agent."""

    description: str
    agent_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    params: dict[str, Any] = field(default_factory=dict)
    state: AgentState = AgentState.CREATED
    result: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "description": self.description,
            "params": self.params,
            "state": self.state.value,
            "result": self.result,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class AgentMessage:
    """A message between agents."""

    source: str
    destination: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize message to dictionary."""
        return {
            "message_id": self.message_id,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class CoordinationPlan:
    """A plan for coordinating multiple agents."""

    mode: CoordinationMode
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agents: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    consensus_threshold: float = 0.7

    def to_dict(self) -> dict[str, Any]:
        """Serialize plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "mode": self.mode.value,
            "agents": self.agents,
            "tasks": self.tasks,
            "consensus_threshold": self.consensus_threshold,
        }
