"""Domain models for the Workforce OS service.

Defines the data structures used by the Workforce OS multi-agent system
for agent type classification, task dispatch, and result reporting.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AgentType(StrEnum):
    """Enumeration of supported agent types in the Workforce OS.

    Each agent type represents a specialized AI agent domain
    that handles specific categories of tasks.
    """

    CODING = "coding"
    RESEARCH = "research"
    PLANNER = "planner"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    SYSTEM = "system"
    VOICE = "voice"
    VISION = "vision"
    WEB = "web"
    ANDROID = "android"
    CUSTOM = "custom"


class AgentStatus(StrEnum):
    """Enumeration of possible agent operational states.

    Tracks the current lifecycle status of a registered agent.
    """

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass(frozen=True)
class AgentTask:
    """A task to be dispatched to an agent for processing.

    Attributes:
        task_id: Unique identifier for this task.
        agent_type: The type of agent best suited to handle this task.
        instruction: The instruction or prompt for the agent to execute.
        context: Optional additional context for the task.
        timeout_seconds: Maximum time allowed for task execution.
        priority: Task priority (1=highest, 10=lowest). Default is 5.
    """

    task_id: str
    agent_type: AgentType
    instruction: str
    context: dict[str, Any] | None = None
    timeout_seconds: int = 120
    priority: int = 5


@dataclass(frozen=True)
class AgentResult:
    """Result produced by an agent after processing a task.

    Attributes:
        task_id: Identifier of the task that produced this result.
        agent_type: The type of agent that processed the task.
        output: The generated output content from the agent.
        status: Completion status of the task (e.g., "success", "error").
        tokens_used: Number of LLM tokens consumed during processing.
        duration_ms: Processing time in milliseconds.
        artifacts: Optional list of artifacts produced (files, data, etc.).
    """

    task_id: str
    agent_type: AgentType
    output: str
    status: str
    tokens_used: int = 0
    duration_ms: float = 0.0
    artifacts: list[dict[str, Any]] | None = None
