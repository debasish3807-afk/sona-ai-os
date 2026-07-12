"""Async event bus — publish/subscribe for kernel events.

Supports typed events, priority ordering, middleware, and
async handlers. Events are delivered in priority order.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from cognitive.kernel_events import EventType, KernelEvent
from config.logging import get_logger

logger = get_logger(__name__)

EventHandler = Callable[[KernelEvent], Coroutine[Any, Any, None]]
Middleware = Callable[[KernelEvent], KernelEvent | None]


class EventBus:
    """Async publish/subscribe event bus for the Cognitive Kernel.

    Features:
        - Typed event subscriptions (by EventType)
        - Priority-ordered delivery
        - Middleware pipeline (transform/filter events)
        - Async handlers with error isolation
        - Event history for debugging
    """

    def __init__(self, max_history: int = 500) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._global_handlers: list[EventHandler] = []
        self._middleware: list[Middleware] = []
        self._history: list[KernelEvent] = []
        self._max_history = max_history
        self._event_count = 0

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def history(self) -> list[KernelEvent]:
        return self._history.copy()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def add_middleware(self, middleware: Middleware) -> None:
        """Add middleware that can transform or filter events."""
        self._middleware.append(middleware)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: KernelEvent) -> None:
        """Publish an event to all subscribers.

        Events pass through middleware before delivery.
        Handler errors are logged but do not propagate.
        """
        # Apply middleware
        processed: KernelEvent | None = event
        for mw in self._middleware:
            if processed is None:
                return  # Middleware filtered the event
            processed = mw(processed)
        if processed is None:
            return

        # Record in history
        self._history.append(processed)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]
        self._event_count += 1

        # Dispatch to type-specific handlers
        handlers = list(self._handlers.get(processed.event_type, []))
        handlers.extend(self._global_handlers)

        for handler in handlers:
            try:
                await handler(processed)
            except Exception as exc:
                logger.warning(
                    "Event handler error",
                    event_type=processed.event_type.value,
                    error=str(exc),
                )

    async def publish_many(self, events: list[KernelEvent]) -> None:
        """Publish multiple events in priority order."""
        sorted_events = sorted(events, key=lambda e: e.priority)
        for event in sorted_events:
            await self.publish(event)

    def get_history(
        self,
        request_id: str | None = None,
        event_type: EventType | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query event history with filters."""
        filtered = self._history
        if request_id:
            filtered = [e for e in filtered if e.request_id == request_id]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        return [e.to_dict() for e in filtered[-limit:]]

    def reset(self) -> None:
        """Clear all handlers and history (for testing)."""
        self._handlers.clear()
        self._global_handlers.clear()
        self._middleware.clear()
        self._history.clear()
        self._event_count = 0
