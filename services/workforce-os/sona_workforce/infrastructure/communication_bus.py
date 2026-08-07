"""Communication Bus - in-memory message bus for agent-to-agent communication."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

import structlog

from sona_workforce.domain.communication import AgentMessage, MessageType

logger = structlog.get_logger()

MessageHandler = Callable[[AgentMessage], Coroutine[Any, Any, None]]


class CommunicationBus:
    """In-memory message bus for agent-to-agent communication.

    Supports: send, broadcast, subscribe, get_messages.
    Each agent has its own message queue.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[AgentMessage]] = defaultdict(list)
        self._subscribers: dict[str, list[MessageHandler]] = defaultdict(list)
        self._broadcast_subscribers: list[MessageHandler] = []
        self._message_count = 0

    async def send(self, message: AgentMessage) -> None:
        """Send a message to a specific agent."""
        self._queues[message.to_agent].append(message)
        self._message_count += 1

        await logger.ainfo(
            "message_sent",
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            message_type=message.message_type,
        )

        # Notify subscribers for the target agent
        for handler in self._subscribers.get(message.to_agent, []):
            await handler(message)

    async def broadcast(self, message: AgentMessage) -> None:
        """Broadcast a message to all agents."""
        # Add to all queues except sender's
        for agent_id in list(self._queues.keys()):
            if agent_id != message.from_agent:
                self._queues[agent_id].append(message)

        self._message_count += 1

        await logger.ainfo(
            "message_broadcast",
            from_agent=message.from_agent,
            message_type=message.message_type,
        )

        # Notify broadcast subscribers
        for handler in self._broadcast_subscribers:
            await handler(message)

    def subscribe(self, agent_id: str, handler: MessageHandler) -> None:
        """Subscribe to messages for a specific agent."""
        self._subscribers[agent_id].append(handler)

    def subscribe_broadcast(self, handler: MessageHandler) -> None:
        """Subscribe to all broadcast messages."""
        self._broadcast_subscribers.append(handler)

    def get_messages(self, agent_id: str) -> list[AgentMessage]:
        """Get all pending messages for an agent."""
        return list(self._queues.get(agent_id, []))

    def get_messages_by_type(self, agent_id: str, message_type: MessageType) -> list[AgentMessage]:
        """Get messages of a specific type for an agent."""
        return [m for m in self._queues.get(agent_id, []) if m.message_type == message_type]

    def clear_messages(self, agent_id: str) -> int:
        """Clear all messages for an agent. Returns count cleared."""
        count = len(self._queues.get(agent_id, []))
        self._queues[agent_id] = []
        return count

    def register_agent(self, agent_id: str) -> None:
        """Register an agent to have a message queue."""
        if agent_id not in self._queues:
            self._queues[agent_id] = []

    @property
    def message_count(self) -> int:
        """Total messages sent through the bus."""
        return self._message_count

    def get_stats(self) -> dict[str, Any]:
        """Get communication bus statistics."""
        return {
            "total_messages": self._message_count,
            "active_queues": len(self._queues),
            "total_subscribers": sum(len(s) for s in self._subscribers.values()),
            "broadcast_subscribers": len(self._broadcast_subscribers),
        }
