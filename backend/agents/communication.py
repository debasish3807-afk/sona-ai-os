"""Inter-agent communication system.

Provides messaging primitives for agents to communicate,
delegate tasks, share results, and coordinate activities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import uuid4


class MessageType(str, Enum):
    """Types of inter-agent messages."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    DELEGATION = "delegation"
    BROADCAST = "broadcast"
    ACK = "acknowledgement"
    ERROR = "error"


class MessagePriority(int, Enum):
    """Message delivery priority."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90


@dataclass
class AgentMessage:
    """A message exchanged between agents.

    Attributes:
        message_id: Unique message identifier.
        message_type: Classification of this message.
        sender_id: The sending agent.
        recipient_id: The target agent (None for broadcast).
        content: Message payload.
        priority: Delivery priority.
        reply_to: Message ID this is replying to.
        correlation_id: For tracking related messages.
        ttl_seconds: Time to live before expiry.
        timestamp: When the message was created.
        metadata: Additional message metadata.
    """

    message_type: MessageType
    sender_id: str
    content: Dict[str, Any]
    recipient_id: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid4()))
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None
    ttl_seconds: Optional[float] = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.recipient_id is None

    @property
    def is_reply(self) -> bool:
        """Check if this is a reply to another message."""
        return self.reply_to is not None



# Type alias for message handlers
MessageHandler = Callable[
    [AgentMessage], Coroutine[Any, Any, Optional[AgentMessage]]
]


class MessageBus(ABC):
    """Abstract interface for inter-agent messaging.

    Provides reliable message delivery between agents with
    support for direct messages, broadcasts, and request/reply.
    """

    @abstractmethod
    async def send(self, message: AgentMessage) -> str:
        """Send a message to a specific agent.

        Args:
            message: The message to send.

        Returns:
            The message_id of the sent message.

        Raises:
            AgentCommunicationError: If delivery fails.
        """
        ...

    @abstractmethod
    async def broadcast(
        self,
        sender_id: str,
        content: Dict[str, Any],
        target_agents: Optional[List[str]] = None,
    ) -> str:
        """Broadcast a message to multiple agents.

        Args:
            sender_id: The broadcasting agent.
            content: Message payload.
            target_agents: Optional list of targets (all if None).

        Returns:
            The message_id of the broadcast.
        """
        ...

    @abstractmethod
    async def request(
        self,
        message: AgentMessage,
        timeout_seconds: float = 30.0,
    ) -> Optional[AgentMessage]:
        """Send a request and wait for a reply.

        Args:
            message: The request message.
            timeout_seconds: Maximum wait time.

        Returns:
            Reply message or None on timeout.
        """
        ...

    @abstractmethod
    async def subscribe(
        self,
        agent_id: str,
        handler: MessageHandler,
        message_types: Optional[List[MessageType]] = None,
    ) -> str:
        """Subscribe an agent to receive messages.

        Args:
            agent_id: The subscribing agent.
            handler: Async handler for incoming messages.
            message_types: Optional filter by message types.

        Returns:
            Subscription identifier.
        """
        ...

    @abstractmethod
    async def unsubscribe(self, agent_id: str) -> bool:
        """Unsubscribe an agent from messages.

        Args:
            agent_id: The agent to unsubscribe.

        Returns:
            True if the subscription was found and removed.
        """
        ...

    @abstractmethod
    async def get_pending(
        self, agent_id: str, limit: int = 10
    ) -> List[AgentMessage]:
        """Get pending messages for an agent.

        Args:
            agent_id: The target agent.
            limit: Maximum messages to return.

        Returns:
            List of pending messages.
        """
        ...
