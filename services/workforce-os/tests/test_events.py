"""Unit tests for domain events."""

from dataclasses import FrozenInstanceError

import pytest

from sona_workforce.domain.events import (
    AgentCommunicationEvent,
    AgentDelegatedEvent,
    AgentRegisteredEvent,
    TaskCompletedEvent,
    TaskDispatchedEvent,
    TaskFailedEvent,
)


class TestAgentRegisteredEvent:
    def test_creation(self) -> None:
        event = AgentRegisteredEvent(
            agent_id="agent-1",
            agent_type="coding",
            capabilities=("code_generation", "code_review"),
        )
        assert event.agent_id == "agent-1"
        assert event.agent_type == "coding"
        assert event.capabilities == ("code_generation", "code_review")

    def test_defaults(self) -> None:
        event = AgentRegisteredEvent()
        assert event.agent_id == ""
        assert event.agent_type == ""
        assert event.capabilities == ()

    def test_frozen(self) -> None:
        event = AgentRegisteredEvent(agent_id="a1")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.agent_id = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        event = AgentRegisteredEvent()
        assert event.event_id is not None
        assert event.occurred_at is not None


class TestTaskDispatchedEvent:
    def test_creation(self) -> None:
        event = TaskDispatchedEvent(
            task_id="task-1",
            agent_id="agent-1",
            agent_type="research",
        )
        assert event.task_id == "task-1"
        assert event.agent_id == "agent-1"
        assert event.agent_type == "research"

    def test_defaults(self) -> None:
        event = TaskDispatchedEvent()
        assert event.task_id == ""
        assert event.agent_id == ""
        assert event.agent_type == ""

    def test_frozen(self) -> None:
        event = TaskDispatchedEvent(task_id="t1")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.task_id = "changed"  # type: ignore[misc]


class TestTaskCompletedEvent:
    def test_creation(self) -> None:
        event = TaskCompletedEvent(
            task_id="t1",
            agent_id="a1",
            duration_ms=150.5,
            tokens_used=500,
        )
        assert event.task_id == "t1"
        assert event.agent_id == "a1"
        assert event.duration_ms == 150.5
        assert event.tokens_used == 500

    def test_defaults(self) -> None:
        event = TaskCompletedEvent()
        assert event.duration_ms == 0.0
        assert event.tokens_used == 0

    def test_frozen(self) -> None:
        event = TaskCompletedEvent(task_id="t1")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.tokens_used = 100  # type: ignore[misc]


class TestTaskFailedEvent:
    def test_creation(self) -> None:
        event = TaskFailedEvent(
            task_id="t1",
            agent_id="a1",
            error="Timeout exceeded",
        )
        assert event.error == "Timeout exceeded"

    def test_defaults(self) -> None:
        event = TaskFailedEvent()
        assert event.error == ""

    def test_frozen(self) -> None:
        event = TaskFailedEvent(error="fail")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.error = "changed"  # type: ignore[misc]


class TestAgentDelegatedEvent:
    def test_creation(self) -> None:
        event = AgentDelegatedEvent(
            from_agent="mgr-1",
            to_agent="worker-1",
            task_id="t1",
        )
        assert event.from_agent == "mgr-1"
        assert event.to_agent == "worker-1"
        assert event.task_id == "t1"

    def test_defaults(self) -> None:
        event = AgentDelegatedEvent()
        assert event.from_agent == ""
        assert event.to_agent == ""
        assert event.task_id == ""

    def test_frozen(self) -> None:
        event = AgentDelegatedEvent(from_agent="a")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.from_agent = "b"  # type: ignore[misc]


class TestAgentCommunicationEvent:
    def test_creation(self) -> None:
        event = AgentCommunicationEvent(
            from_agent="a1",
            to_agent="a2",
            message_type="request",
        )
        assert event.from_agent == "a1"
        assert event.to_agent == "a2"
        assert event.message_type == "request"

    def test_defaults(self) -> None:
        event = AgentCommunicationEvent()
        assert event.from_agent == ""
        assert event.message_type == ""

    def test_frozen(self) -> None:
        event = AgentCommunicationEvent(message_type="event")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            event.message_type = "changed"  # type: ignore[misc]
