"""IPC protocol — message envelope creation and validation."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from microkernel.schemas import IPCMessage, MessagePriority


@dataclass
class IPCChannel:
    """A communication channel between two endpoints."""

    channel_id: str
    source: str
    destination: str
    created_at: float = field(default_factory=time.time)
    message_count: int = 0
    active: bool = True


@dataclass
class DeadLetter:
    """An undeliverable message stored for inspection."""

    original_message: IPCMessage
    reason: str
    failed_at: float = field(default_factory=time.time)
    retry_count: int = 0


class MessageEnvelope:
    """Factory for creating well-formed IPC messages."""

    @staticmethod
    def create_request(
        source: str,
        destination: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str | None = None,
    ) -> IPCMessage:
        """Create a new request message."""
        return IPCMessage(
            source=source,
            destination=destination,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
        )

    @staticmethod
    def create_response(request: IPCMessage, payload: dict[str, Any]) -> IPCMessage:
        """Create a response to an existing request."""
        return IPCMessage(
            source=request.destination,
            destination=request.source,
            payload=payload,
            correlation_id=request.correlation_id,
            request_id=request.request_id,
            priority=request.priority,
        )

    @staticmethod
    def create_broadcast(
        source: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> IPCMessage:
        """Create a broadcast message to all subscribers."""
        return IPCMessage(
            source=source,
            destination="*",
            payload=payload,
            priority=priority,
            correlation_id=str(uuid.uuid4()),
        )

    @staticmethod
    def validate(message: IPCMessage) -> tuple[bool, list[str]]:
        """Validate a message for correctness."""
        errors: list[str] = []
        if not message.source:
            errors.append("source is required")
        if not message.destination:
            errors.append("destination is required")
        if not message.message_id:
            errors.append("message_id is required")
        if message.ttl_seconds <= 0:
            errors.append("ttl_seconds must be positive")
        if message.timestamp <= 0:
            errors.append("timestamp must be positive")
        return (len(errors) == 0, errors)
