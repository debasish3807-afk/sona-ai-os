"""Agent domain model with capabilities and state management."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AgentRole(StrEnum):
    """Role classification for agents in the workforce hierarchy."""

    MANAGER = "manager"
    WORKER = "worker"
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"


class AgentCapability(StrEnum):
    """Capabilities that agents can possess."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    RESEARCH = "research"
    PLANNING = "planning"
    WRITING = "writing"
    SUMMARIZATION = "summarization"
    DATA_ANALYSIS = "data_analysis"
    MEMORY_MANAGEMENT = "memory_management"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    TASK_EXECUTION = "task_execution"
    DELEGATION = "delegation"
    QUALITY_REVIEW = "quality_review"


class AgentState(StrEnum):
    """Operational states for an agent."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    DELEGATING = "delegating"
    WAITING = "waiting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentProfile:
    """Profile describing an agent's identity, capabilities, and current state."""

    agent_id: str
    name: str
    agent_type: str  # AgentType value
    role: AgentRole
    capabilities: list[AgentCapability]
    state: AgentState = AgentState.IDLE
    max_concurrent_tasks: int = 3
    priority: int = 5
    active_tasks: int = 0
    total_completed: int = 0
    total_failed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
