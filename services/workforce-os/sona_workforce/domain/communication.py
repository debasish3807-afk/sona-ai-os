"""Agent communication models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MessageType(StrEnum):
    """Types of messages exchanged between agents."""

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    EVENT = "event"
    DELEGATION = "delegation"


@dataclass(frozen=True)
class AgentMessage:
    """A message exchanged between agents.

    Attributes:
        message_id: Unique identifier for this message.
        from_agent: ID of the sending agent.
        to_agent: ID of the receiving agent.
        message_type: The type of message.
        content: The message content.
        context: Optional additional context.
        priority: Message priority (1=highest, 10=lowest).
    """

    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
