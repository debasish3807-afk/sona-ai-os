"""Unit tests for AgentMessage and MessageType."""

from dataclasses import FrozenInstanceError

import pytest

from sona_workforce.domain.communication import AgentMessage, MessageType


class TestMessageType:
    def test_all_values(self) -> None:
        expected = {"REQUEST", "RESPONSE", "BROADCAST", "EVENT", "DELEGATION"}
        actual = {m.name for m in MessageType}
        assert actual == expected

    def test_string_values(self) -> None:
        assert MessageType.REQUEST == "request"
        assert MessageType.RESPONSE == "response"
        assert MessageType.BROADCAST == "broadcast"
        assert MessageType.EVENT == "event"
        assert MessageType.DELEGATION == "delegation"

    def test_is_str_enum(self) -> None:
        assert isinstance(MessageType.REQUEST, str)

    def test_count(self) -> None:
        assert len(MessageType) == 5


class TestAgentMessage:
    def test_creation(self) -> None:
        msg = AgentMessage(
            message_id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            message_type=MessageType.REQUEST,
            content="Hello",
        )
        assert msg.message_id == "msg-1"
        assert msg.from_agent == "agent-1"
        assert msg.to_agent == "agent-2"
        assert msg.message_type == MessageType.REQUEST
        assert msg.content == "Hello"

    def test_default_context(self) -> None:
        msg = AgentMessage(
            message_id="m1",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.EVENT,
            content="test",
        )
        assert msg.context == {}
        assert msg.priority == 5

    def test_with_context(self) -> None:
        ctx = {"task_id": "t1", "urgency": "high"}
        msg = AgentMessage(
            message_id="m1",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.DELEGATION,
            content="delegate this",
            context=ctx,
            priority=1,
        )
        assert msg.context == ctx
        assert msg.priority == 1

    def test_is_frozen(self) -> None:
        msg = AgentMessage(
            message_id="m1",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.RESPONSE,
            content="ok",
        )
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            msg.content = "changed"  # type: ignore[misc]

    def test_all_message_types(self) -> None:
        for mt in MessageType:
            msg = AgentMessage(
                message_id=f"m-{mt.value}",
                from_agent="a1",
                to_agent="a2",
                message_type=mt,
                content="test",
            )
            assert msg.message_type == mt

    def test_broadcast_message(self) -> None:
        msg = AgentMessage(
            message_id="broadcast-1",
            from_agent="manager",
            to_agent="all",
            message_type=MessageType.BROADCAST,
            content="System update",
        )
        assert msg.to_agent == "all"
        assert msg.message_type == MessageType.BROADCAST

    def test_context_independence(self) -> None:
        msg1 = AgentMessage(
            message_id="m1",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.REQUEST,
            content="t",
        )
        msg2 = AgentMessage(
            message_id="m2",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.REQUEST,
            content="t",
        )
        # Frozen, so context is independent by default
        assert msg1.context is not msg2.context
