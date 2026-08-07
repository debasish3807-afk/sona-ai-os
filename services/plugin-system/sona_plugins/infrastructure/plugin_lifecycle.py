"""Plugin lifecycle manager — enforces state machine transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

from sona_plugins.domain.events import (
    PluginActivatedEvent,
    PluginDeactivatedEvent,
    PluginFailedEvent,
)
from sona_plugins.domain.lifecycle import VALID_TRANSITIONS, PluginLifecycleState

logger = structlog.get_logger()


@dataclass
class LifecycleTransitionRecord:
    """Records a single lifecycle state transition."""

    plugin_id: str
    from_state: PluginLifecycleState
    to_state: PluginLifecycleState
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    reason: str = ""


class InvalidTransitionError(Exception):
    """Raised when an invalid lifecycle state transition is attempted."""

    def __init__(
        self,
        plugin_id: str,
        from_state: PluginLifecycleState,
        to_state: PluginLifecycleState,
    ) -> None:
        self.plugin_id = plugin_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition for plugin '{plugin_id}': {from_state} -> {to_state}")


class PluginLifecycleManager:
    """Manages plugin lifecycle transitions and history.

    Enforces the state machine defined in VALID_TRANSITIONS,
    records transition history, and emits domain events.
    """

    def __init__(self) -> None:
        self._states: dict[str, PluginLifecycleState] = {}
        self._history: dict[str, list[LifecycleTransitionRecord]] = {}
        self._events: list[PluginActivatedEvent | PluginDeactivatedEvent | PluginFailedEvent] = []

    def register(
        self,
        plugin_id: str,
        initial_state: PluginLifecycleState = PluginLifecycleState.DISCOVERED,
    ) -> None:
        """Register a plugin with the lifecycle manager."""
        self._states[plugin_id] = initial_state
        self._history[plugin_id] = []
        logger.info("lifecycle_registered", plugin_id=plugin_id, initial_state=initial_state)

    def get_state(self, plugin_id: str) -> PluginLifecycleState | None:
        """Get the current lifecycle state of a plugin."""
        return self._states.get(plugin_id)

    def transition(self, plugin_id: str, to_state: PluginLifecycleState, reason: str = "") -> None:
        """Transition a plugin to a new lifecycle state.

        Raises:
            InvalidTransitionError: If the transition is not valid.
            ValueError: If the plugin is not registered.
        """
        current = self._states.get(plugin_id)
        if current is None:
            raise ValueError(f"Plugin not registered: {plugin_id}")

        valid_targets = VALID_TRANSITIONS.get(current, [])
        if to_state not in valid_targets:
            raise InvalidTransitionError(plugin_id, current, to_state)

        record = LifecycleTransitionRecord(
            plugin_id=plugin_id,
            from_state=current,
            to_state=to_state,
            reason=reason,
        )
        self._history[plugin_id].append(record)
        self._states[plugin_id] = to_state

        # Emit domain events for key transitions
        if to_state == PluginLifecycleState.RUNNING:
            self._events.append(PluginActivatedEvent(plugin_id=plugin_id))
        elif to_state == PluginLifecycleState.STOPPED:
            self._events.append(PluginDeactivatedEvent(plugin_id=plugin_id, reason=reason))
        elif to_state == PluginLifecycleState.ERROR:
            self._events.append(PluginFailedEvent(plugin_id=plugin_id, error=reason, state=current))

        logger.info(
            "lifecycle_transition",
            plugin_id=plugin_id,
            from_state=current,
            to_state=to_state,
            reason=reason,
        )

    def can_transition(self, plugin_id: str, to_state: PluginLifecycleState) -> bool:
        """Check if a transition to the given state is valid."""
        current = self._states.get(plugin_id)
        if current is None:
            return False
        return to_state in VALID_TRANSITIONS.get(current, [])

    def get_history(self, plugin_id: str) -> list[LifecycleTransitionRecord]:
        """Get the transition history for a plugin."""
        return list(self._history.get(plugin_id, []))

    def drain_events(
        self,
    ) -> list[PluginActivatedEvent | PluginDeactivatedEvent | PluginFailedEvent]:
        """Drain and return all pending domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from lifecycle management."""
        self._states.pop(plugin_id, None)
        self._history.pop(plugin_id, None)

    def get_all_states(self) -> dict[str, PluginLifecycleState]:
        """Get all registered plugin states."""
        return dict(self._states)
