"""Agent event system.

Defines events emitted by agents and the agent framework for
decoupled communication and monitoring.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class AgentEvents:
    """Standard event type constants for agent operations."""

    # Lifecycle events
    AGENT_REGISTERED = "agent.lifecycle.registered"
    AGENT_UNREGISTERED = "agent.lifecycle.unregistered"
    AGENT_INITIALIZED = "agent.lifecycle.initialized"
    AGENT_STARTED = "agent.lifecycle.started"
    AGENT_STOPPED = "agent.lifecycle.stopped"
    AGENT_ERROR = "agent.lifecycle.error"

    # Execution events
    TASK_ASSIGNED = "agent.execution.task_assigned"
    TASK_STARTED = "agent.execution.task_started"
    TASK_COMPLETED = "agent.execution.task_completed"
    TASK_FAILED = "agent.execution.task_failed"
    TASK_DELEGATED = "agent.execution.task_delegated"
    TASK_CANCELLED = "agent.execution.task_cancelled"

    # Communication events
    MESSAGE_SENT = "agent.communication.message_sent"
    MESSAGE_RECEIVED = "agent.communication.message_received"
    BROADCAST_SENT = "agent.communication.broadcast_sent"

    # Coordination events
    WORKFLOW_STARTED = "agent.workflow.started"
    WORKFLOW_STEP_COMPLETED = "agent.workflow.step_completed"
    WORKFLOW_COMPLETED = "agent.workflow.completed"
    WORKFLOW_FAILED = "agent.workflow.failed"

    # Health events
    HEALTH_CHANGED = "agent.health.changed"
    HEALTH_DEGRADED = "agent.health.degraded"
    HEALTH_RECOVERED = "agent.health.recovered"


@dataclass(frozen=True)
class AgentEvent:
    """An event emitted by the agent system.

    Attributes:
        event_type: The event type identifier.
        agent_id: The agent that emitted the event.
        event_id: Unique event identifier.
        timestamp: When the event was created.
        data: Event payload data.
        correlation_id: For correlating related events.
        metadata: Additional event metadata.
    """

    event_type: str
    agent_id: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
