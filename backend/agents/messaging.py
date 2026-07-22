"""Inter-agent messaging system — asynchronous communication between agents."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class MessageType(str, Enum):
    """Types of inter-agent messages."""

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    DELEGATE = "delegate"
    RESULT = "result"


class MessagePriority(str, Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    """A message sent between agents."""

    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    sender_id: str = ""
    recipient_id: str = ""
    correlation_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: float = 60.0

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl_seconds


class MessageBus:
    """Asynchronous message bus for inter-agent communication.

    Supports direct messages (agent-to-agent), broadcasts (one-to-many),
    and request/response patterns with correlation IDs.
    """

    def __init__(self) -> None:
        self._inboxes: dict[str, list[AgentMessage]] = defaultdict(list)
        self._subscriptions: dict[str, list[str]] = defaultdict(list)  # topic -> agent_ids
        self._total_sent = 0
        self._total_expired = 0

    async def send(self, message: AgentMessage) -> str:
        """Send a message to a specific agent."""
        self._inboxes[message.recipient_id].append(message)
        self._total_sent += 1
        return message.msg_id

    async def broadcast(self, message: AgentMessage, agent_ids: list[str]) -> list[str]:
        """Broadcast a message to multiple agents."""
        ids = []
        for aid in agent_ids:
            msg = AgentMessage(
                msg_type=MessageType.BROADCAST,
                sender_id=message.sender_id,
                recipient_id=aid,
                payload=message.payload,
                correlation_id=message.correlation_id,
            )
            self._inboxes[aid].append(msg)
            ids.append(msg.msg_id)
            self._total_sent += 1
        return ids

    async def request(
        self,
        sender_id: str,
        recipient_id: str,
        payload: dict[str, Any],
        correlation_id: str = "",
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        """Send a request and wait for a response."""
        corr_id = correlation_id or str(uuid.uuid4())
        req = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            correlation_id=corr_id,
            ttl_seconds=timeout,
        )
        await self.send(req)
        deadline = time.time() + timeout
        while time.time() < deadline:
            for i, msg in enumerate(self._inboxes.get(sender_id, [])):
                if msg.correlation_id == corr_id and msg.msg_type == MessageType.RESPONSE:
                    self._inboxes[sender_id].pop(i)
                    return msg
            import asyncio

            await asyncio.sleep(0.1)
        return None

    async def respond(self, original: AgentMessage, payload: dict[str, Any]) -> str:
        """Respond to a request message."""
        resp = AgentMessage(
            msg_type=MessageType.RESPONSE,
            sender_id=original.recipient_id,
            recipient_id=original.sender_id,
            payload=payload,
            correlation_id=original.correlation_id,
        )
        return await self.send(resp)

    async def receive(self, agent_id: str) -> list[AgentMessage]:
        """Receive all pending messages for an agent."""
        messages = self._inboxes.get(agent_id, [])
        valid = [m for m in messages if not m.is_expired()]
        expired = len(messages) - len(valid)
        self._total_expired += expired
        self._inboxes[agent_id] = valid
        return valid

    async def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic."""
        if agent_id not in self._subscriptions[topic]:
            self._subscriptions[topic].append(agent_id)

    async def publish(self, topic: str, payload: dict[str, Any], sender_id: str = "") -> list[str]:
        """Publish a message to all subscribers of a topic."""
        subscribers = self._subscriptions.get(topic, [])
        msg = AgentMessage(
            msg_type=MessageType.BROADCAST,
            sender_id=sender_id,
            payload=payload,
            correlation_id=topic,
        )
        for aid in subscribers:
            self._inboxes[aid].append(msg)
            self._total_sent += 1
        return subscribers

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_sent": self._total_sent,
            "total_expired": self._total_expired,
            "inboxes": {k: len(v) for k, v in self._inboxes.items() if v},
            "subscriptions": {k: len(v) for k, v in self._subscriptions.items()},
        }
