"""Event bus system for kernel-wide communication.

Provides a publish/subscribe event system for decoupled communication
between kernel components. Supports both synchronous and asynchronous
event handlers with priority ordering.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from uuid import uuid4


class EventPriority(int, Enum):
    """Event handler execution priority.

    Lower values execute first.
    """

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    BACKGROUND = 100


class EventStatus(str, Enum):
    """Status of an event in its lifecycle."""

    PENDING = "pending"
    DISPATCHING = "dispatching"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Event:
    """Base event data class.

    All events in the system inherit from this. Events are immutable
    once created to ensure consistency across handlers.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: Dot-notation event type (e.g., 'kernel.started').
        timestamp: UTC timestamp when the event was created.
        source: Identifier of the component that emitted the event.
        data: Arbitrary event payload.
        correlation_id: Optional ID for correlating related events.
        metadata: Additional event metadata.
    """

    event_type: str
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """Represents a subscription to an event type.

    Attributes:
        subscription_id: Unique subscription identifier.
        event_type: Event type pattern to match (supports wildcards).
        handler: Async callable to invoke when event matches.
        priority: Execution priority for ordering.
        filter_fn: Optional filter function for conditional handling.
        max_retries: Maximum retry attempts on handler failure.
        active: Whether this subscription is currently active.
    """

    event_type: str
    handler: Callable[..., Coroutine[Any, Any, None]]
    subscription_id: str = field(default_factory=lambda: str(uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    filter_fn: Optional[Callable[[Event], bool]] = None
    max_retries: int = 0
    active: bool = True


@dataclass
class EventResult:
    """Result of dispatching an event.

    Attributes:
        event: The original event that was dispatched.
        status: Final status after dispatch.
        handlers_invoked: Number of handlers that were called.
        handlers_succeeded: Number of handlers that completed successfully.
        handlers_failed: Number of handlers that raised exceptions.
        errors: List of error details from failed handlers.
        duration_ms: Total dispatch duration in milliseconds.
    """

    event: Event
    status: EventStatus = EventStatus.PENDING
    handlers_invoked: int = 0
    handlers_succeeded: int = 0
    handlers_failed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


class EventBus(ABC):
    """Abstract event bus interface.

    Defines the contract for publish/subscribe event systems.
    Implementations handle event routing, handler management,
    and delivery guarantees.
    """

    @abstractmethod
    async def publish(self, event: Event) -> EventResult:
        """Publish an event to all matching subscribers.

        Dispatches the event to all active subscriptions that match
        the event type, respecting priority ordering.

        Args:
            event: The event to publish.

        Returns:
            EventResult with dispatch outcome details.
        """
        ...

    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: Callable[..., Coroutine[Any, Any, None]],
        priority: EventPriority = EventPriority.NORMAL,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> EventSubscription:
        """Subscribe a handler to an event type.

        The handler will be invoked whenever a matching event is published.
        Supports wildcard patterns (e.g., 'kernel.*' matches all kernel events).

        Args:
            event_type: Event type pattern to subscribe to.
            handler: Async callable to invoke on matching events.
            priority: Execution priority for ordering handlers.
            filter_fn: Optional filter for conditional invocation.

        Returns:
            EventSubscription representing the active subscription.
        """
        ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by ID.

        Args:
            subscription_id: The subscription to remove.

        Returns:
            True if the subscription was found and removed.
        """
        ...

    @abstractmethod
    async def unsubscribe_all(self, event_type: str) -> int:
        """Remove all subscriptions for an event type.

        Args:
            event_type: Event type to clear subscriptions for.

        Returns:
            Number of subscriptions removed.
        """
        ...

    @abstractmethod
    def get_subscriptions(self, event_type: Optional[str] = None) -> List[EventSubscription]:
        """Get active subscriptions, optionally filtered by event type.

        Args:
            event_type: Optional event type to filter by.

        Returns:
            List of matching active subscriptions.
        """
        ...

    @abstractmethod
    def get_event_types(self) -> Set[str]:
        """Get all registered event types with active subscriptions.

        Returns:
            Set of event type strings.
        """
        ...


class EventEmitter(ABC):
    """Mixin interface for components that emit events.

    Components that produce events should implement this interface
    to provide consistent event emission capabilities.
    """

    @abstractmethod
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for emitting events.

        Args:
            event_bus: The event bus to publish events to.
        """
        ...

    @abstractmethod
    async def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event through the configured event bus.

        Args:
            event_type: Type identifier for the event.
            data: Optional event payload data.
        """
        ...


# Standard kernel event types
class KernelEvents:
    """Standard event type constants for kernel operations."""

    # Lifecycle events
    KERNEL_STARTING = "kernel.lifecycle.starting"
    KERNEL_STARTED = "kernel.lifecycle.started"
    KERNEL_STOPPING = "kernel.lifecycle.stopping"
    KERNEL_STOPPED = "kernel.lifecycle.stopped"

    # Task events
    TASK_CREATED = "kernel.task.created"
    TASK_STARTED = "kernel.task.started"
    TASK_COMPLETED = "kernel.task.completed"
    TASK_FAILED = "kernel.task.failed"
    TASK_CANCELLED = "kernel.task.cancelled"

    # Session events
    SESSION_CREATED = "kernel.session.created"
    SESSION_UPDATED = "kernel.session.updated"
    SESSION_CLOSED = "kernel.session.closed"

    # Provider events
    PROVIDER_REGISTERED = "kernel.provider.registered"
    PROVIDER_UNREGISTERED = "kernel.provider.unregistered"
    PROVIDER_HEALTH_CHANGED = "kernel.provider.health_changed"

    # Model events
    MODEL_SELECTED = "kernel.model.selected"
    MODEL_FALLBACK = "kernel.model.fallback"

    # Error events
    ERROR_OCCURRED = "kernel.error.occurred"
    ERROR_RECOVERED = "kernel.error.recovered"
