"""Event Bus — publish/subscribe architecture for internal events."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)

Handler = Callable[..., Any]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = {}
        self._history: list[dict[str, Any]] = []
        self._max_history = 500

    def subscribe(self, event_type: str, handler: Handler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> bool:
        if event_type not in self._subscribers:
            return False
        try:
            self._subscribers[event_type].remove(handler)
            return True
        except ValueError:
            return False

    async def publish(self, event_type: str, data: dict[str, Any] | None = None) -> int:
        entry = {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "data": data or {},
            "timestamp": time.time(),
        }
        self._history.insert(0, entry)
        while len(self._history) > self._max_history:
            self._history.pop()
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                result = handler(event_type=event_type, data=data or {})
                if hasattr(result, "__await__"):
                    await result
            except Exception as exc:
                logger.error("event_handler_failed", event_type=event_type, error=str(exc))
        return len(handlers)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._history[:limit]

    def get_subscribers(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._subscribers.items()}

    def get_stats(self) -> dict[str, int]:
        return {
            "events": len(self._history),
            "topics": len(self._subscribers),
            "handlers": sum(len(h) for h in self._subscribers.values()),
        }
