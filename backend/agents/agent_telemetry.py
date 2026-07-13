"""Telemetry collection for the agent system."""

from __future__ import annotations

from typing import Any

from agents.events import AgentEvent
from config.logging import get_logger

logger = get_logger(__name__)


class AgentTelemetry:
    """Collects and queries agent telemetry events."""

    def __init__(self) -> None:
        self._events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        """Emit a telemetry event."""
        self._events.append(event)
        logger.debug("telemetry_event", event_type=event.event_type.value, agent_id=event.agent_id)

    def get_events(self, agent_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get events, optionally filtered by agent."""
        filtered = self._events
        if agent_id:
            filtered = [e for e in filtered if e.agent_id == agent_id]
        return [e.to_dict() for e in filtered[-limit:]]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of collected telemetry."""
        by_type: dict[str, int] = {}
        for event in self._events:
            key = event.event_type.value
            by_type[key] = by_type.get(key, 0) + 1
        return {
            "total_events": len(self._events),
            "by_type": by_type,
        }
