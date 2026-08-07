"""Unit tests for CommunicationBus."""

import pytest

from sona_workforce.domain.communication import AgentMessage, MessageType
from sona_workforce.infrastructure.communication_bus import CommunicationBus


def _msg(
    msg_id: str = "m1",
    from_agent: str = "a1",
    to_agent: str = "a2",
    msg_type: MessageType = MessageType.REQUEST,
    content: str = "hello",
) -> AgentMessage:
    return AgentMessage(
        message_id=msg_id,
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=msg_type,
        content=content,
    )


class TestCommunicationBus:
    @pytest.fixture
    def bus(self) -> CommunicationBus:
        bus = CommunicationBus()
        bus.register_agent("a1")
        bus.register_agent("a2")
        bus.register_agent("a3")
        return bus

    @pytest.mark.asyncio
    async def test_send_message(self, bus: CommunicationBus) -> None:
        msg = _msg()
        await bus.send(msg)
        messages = bus.get_messages("a2")
        assert len(messages) == 1
        assert messages[0].content == "hello"

    @pytest.mark.asyncio
    async def test_broadcast(self, bus: CommunicationBus) -> None:
        msg = _msg(to_agent="all", msg_type=MessageType.BROADCAST)
        await bus.broadcast(msg)
        # a2 and a3 should get it, but not a1 (sender)
        assert len(bus.get_messages("a2")) == 1
        assert len(bus.get_messages("a3")) == 1
        assert len(bus.get_messages("a1")) == 0

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, bus: CommunicationBus) -> None:
        assert bus.get_messages("a1") == []

    @pytest.mark.asyncio
    async def test_get_messages_by_type(self, bus: CommunicationBus) -> None:
        await bus.send(_msg(msg_id="m1", msg_type=MessageType.REQUEST))
        await bus.send(_msg(msg_id="m2", msg_type=MessageType.EVENT))
        result = bus.get_messages_by_type("a2", MessageType.REQUEST)
        assert len(result) == 1
        assert result[0].message_id == "m1"

    @pytest.mark.asyncio
    async def test_clear_messages(self, bus: CommunicationBus) -> None:
        await bus.send(_msg())
        await bus.send(_msg(msg_id="m2"))
        cleared = bus.clear_messages("a2")
        assert cleared == 2
        assert bus.get_messages("a2") == []

    @pytest.mark.asyncio
    async def test_subscribe(self, bus: CommunicationBus) -> None:
        received: list[AgentMessage] = []

        async def handler(msg: AgentMessage) -> None:
            received.append(msg)

        bus.subscribe("a2", handler)
        await bus.send(_msg())
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_subscribe_broadcast(self, bus: CommunicationBus) -> None:
        received: list[AgentMessage] = []

        async def handler(msg: AgentMessage) -> None:
            received.append(msg)

        bus.subscribe_broadcast(handler)
        await bus.broadcast(_msg(msg_type=MessageType.BROADCAST))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_message_count(self, bus: CommunicationBus) -> None:
        assert bus.message_count == 0
        await bus.send(_msg())
        assert bus.message_count == 1
        await bus.send(_msg(msg_id="m2"))
        assert bus.message_count == 2

    def test_register_agent(self) -> None:
        bus = CommunicationBus()
        bus.register_agent("new-agent")
        assert bus.get_messages("new-agent") == []

    @pytest.mark.asyncio
    async def test_get_stats(self, bus: CommunicationBus) -> None:
        await bus.send(_msg())
        stats = bus.get_stats()
        assert stats["total_messages"] == 1
        assert stats["active_queues"] == 3

    @pytest.mark.asyncio
    async def test_multiple_messages(self, bus: CommunicationBus) -> None:
        for i in range(5):
            await bus.send(_msg(msg_id=f"m{i}"))
        messages = bus.get_messages("a2")
        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_message_priority(self, bus: CommunicationBus) -> None:
        msg = AgentMessage(
            message_id="m1",
            from_agent="a1",
            to_agent="a2",
            message_type=MessageType.REQUEST,
            content="urgent",
            priority=1,
        )
        await bus.send(msg)
        result = bus.get_messages("a2")
        assert result[0].priority == 1

    @pytest.mark.asyncio
    async def test_clear_returns_zero_for_empty(self, bus: CommunicationBus) -> None:
        cleared = bus.clear_messages("a1")
        assert cleared == 0
