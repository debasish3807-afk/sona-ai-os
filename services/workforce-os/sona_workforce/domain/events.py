"""Domain events for the Workforce OS service."""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class AgentRegisteredEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a new agent is registered in the workforce."""

    agent_id: str = ""
    agent_type: str = ""
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskDispatchedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a task is dispatched to an agent."""

    task_id: str = ""
    agent_id: str = ""
    agent_type: str = ""


@dataclass(frozen=True)
class TaskCompletedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an agent completes a task."""

    task_id: str = ""
    agent_id: str = ""
    duration_ms: float = 0.0
    tokens_used: int = 0


@dataclass(frozen=True)
class TaskFailedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an agent fails to complete a task."""

    task_id: str = ""
    agent_id: str = ""
    error: str = ""


@dataclass(frozen=True)
class AgentDelegatedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an agent delegates a task to another agent."""

    from_agent: str = ""
    to_agent: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class AgentCommunicationEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when agents communicate with each other."""

    from_agent: str = ""
    to_agent: str = ""
    message_type: str = ""
