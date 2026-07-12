"""IPC Bus — asynchronous message routing for the microkernel."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from config.logging import get_logger
from microkernel.ipc_protocol import DeadLetter, IPCChannel, MessageEnvelope
from microkernel.schemas import IPCMessage, MessagePriority

logger = get_logger(__name__)


class IPCBus:
    """Asynchronous inter-process communication bus.

    Routes messages between microkernel components, manages
    channels, dead-letter queue, and subscriber dispatch.
    """

    def __init__(self) -> None:
        self._channels: dict[str, IPCChannel] = {}
        self._subscribers: dict[str, list[Callable[..., Any]]] = {}
        self._queue: list[IPCMessage] = []
        self._dead_letters: list[DeadLetter] = []
        self._message_count: int = 0

    async def send(self, message: IPCMessage) -> bool:
        """Send a message to its destination channel."""
        valid, errors = MessageEnvelope.validate(message)
        if not valid:
            self._dead_letters.append(
                DeadLetter(
                    original_message=message,
                    reason=f"validation failed: {', '.join(errors)}",
                    failed_at=time.time(),
                )
            )
            logger.warning("ipc_message_invalid", errors=errors)
            return False

        channel_id = message.destination
        if channel_id not in self._channels:
            self._channels[channel_id] = IPCChannel(
                channel_id=channel_id,
                source=message.source,
                destination=message.destination,
                created_at=time.time(),
            )

        self._channels[channel_id].message_count += 1
        self._message_count += 1

        handlers = self._subscribers.get(channel_id, [])
        if not handlers:
            self._queue.append(message)
            return True

        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.error("ipc_handler_error", handler=str(handler), error=str(exc))
                self._dead_letters.append(
                    DeadLetter(
                        original_message=message,
                        reason=f"handler error: {exc}",
                        failed_at=time.time(),
                    )
                )

        return True

    async def request(
        self,
        source: str,
        destination: str,
        payload: dict[str, Any],
        timeout: float = 30.0,
    ) -> IPCMessage | None:
        """Send a request and wait for a response."""
        message = MessageEnvelope.create_request(source, destination, payload)
        response_event: asyncio.Event = asyncio.Event()
        response_holder: list[IPCMessage] = []

        def _response_handler(msg: IPCMessage) -> None:
            if msg.correlation_id == message.correlation_id:
                response_holder.append(msg)
                response_event.set()

        self.subscribe(source, _response_handler)
        await self.send(message)

        try:
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
        except TimeoutError:
            self._dead_letters.append(
                DeadLetter(
                    original_message=message,
                    reason="request timed out",
                    failed_at=time.time(),
                )
            )
            return None
        finally:
            self.unsubscribe(source, _response_handler)

        return response_holder[0] if response_holder else None

    def subscribe(self, channel: str, handler: Callable[..., Any]) -> None:
        """Subscribe a handler to a channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(handler)

    def unsubscribe(self, channel: str, handler: Callable[..., Any]) -> None:
        """Remove a handler from a channel."""
        if channel in self._subscribers:
            try:
                self._subscribers[channel].remove(handler)
            except ValueError:
                logger.debug("ipc_unsubscribe_not_found", channel=channel)

    async def broadcast(
        self,
        source: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """Broadcast a message to all subscribers. Returns delivery count."""
        message = MessageEnvelope.create_broadcast(source, payload, priority)
        delivered = 0

        for channel, handlers in self._subscribers.items():
            for handler in handlers:
                try:
                    result = handler(message)
                    if asyncio.iscoroutine(result):
                        await result
                    delivered += 1
                except Exception as exc:
                    logger.error("ipc_broadcast_error", channel=channel, error=str(exc))

        self._message_count += 1
        return delivered

    def get_dead_letters(self, limit: int = 50) -> list[DeadLetter]:
        """Retrieve dead letters for inspection."""
        return self._dead_letters[:limit]

    def get_channel_stats(self) -> dict[str, Any]:
        """Get statistics about all channels."""
        return {
            "total_channels": len(self._channels),
            "total_subscribers": sum(len(h) for h in self._subscribers.values()),
            "total_messages": self._message_count,
            "dead_letters": len(self._dead_letters),
            "queue_depth": len(self._queue),
            "channels": {
                cid: {"message_count": ch.message_count, "active": ch.active}
                for cid, ch in self._channels.items()
            },
        }

    def get_queue_depth(self) -> int:
        """Return the number of undelivered messages in the queue."""
        return len(self._queue)

    def clear_dead_letters(self) -> int:
        """Clear all dead letters. Returns count cleared."""
        count = len(self._dead_letters)
        self._dead_letters.clear()
        return count
