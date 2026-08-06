"""Abstract port interfaces for the Event Bus library.

Defines the EventPublisherPort and EventSubscriberPort abstract base classes
that all event bus implementations must satisfy, enabling decoupled
service-to-service communication through domain events.
"""

from abc import ABC, abstractmethod
from typing import Type

from sona_shared.domain.primitives import DomainEvent

from sona_events.protocols import AsyncEventHandler


class EventPublisherPort(ABC):
    """Abstract port for publishing domain events.

    Services use this port to emit domain events without any knowledge
    of which other services or handlers will consume them.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers.

        Args:
            event: The domain event to publish. All handlers registered
                   for this event type (and its parent types) will be invoked.
        """
        ...

    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events in sequence.

        Provides a more efficient path for emitting multiple related events
        (e.g., all events from a single aggregate operation).

        Args:
            events: List of domain events to publish in order.
        """
        ...


class EventSubscriberPort(ABC):
    """Abstract port for subscribing to domain events.

    Services use this port to register interest in specific event types.
    Handlers are invoked asynchronously when matching events are published.
    """

    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: AsyncEventHandler,
    ) -> None:
        """Register a handler for a specific domain event type.

        The handler will be called for every published event that is an
        instance of the given event_type (including subclasses).

        Args:
            event_type: The DomainEvent subtype to subscribe to.
            handler: An async callable that will be invoked with matching events.
        """
        ...

    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: AsyncEventHandler,
    ) -> None:
        """Remove a previously registered event handler.

        If the handler is not currently registered for the given event type,
        this is a no-op (does not raise an error).

        Args:
            event_type: The DomainEvent subtype to unsubscribe from.
            handler: The handler callable to remove.
        """
        ...

    @abstractmethod
    def get_subscribers(
        self,
        event_type: Type[DomainEvent],
    ) -> list[AsyncEventHandler]:
        """Retrieve all handlers registered for a specific event type.

        Useful for inspection, testing, and diagnostics.

        Args:
            event_type: The DomainEvent subtype to query.

        Returns:
            List of registered async handler callables.
        """
        ...


class EventBusPort(EventPublisherPort, EventSubscriberPort, ABC):
    """Combined event bus port providing both publishing and subscription.

    Most event bus implementations will provide both capabilities through
    a single object. Services that only need to publish or subscribe
    can depend on the narrower EventPublisherPort or EventSubscriberPort.

    Lifecycle::

        await bus.start()   # Connect to broker, initialise subscriptions
        ...                 # Normal operation
        await bus.stop()    # Drain pending events, disconnect cleanly
    """

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus and establish broker connections.

        Must be called before any publish or subscribe operations.
        Implementations should perform connection setup, channel creation,
        and any other initialisation work here.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus and release all resources.

        Implementations should drain in-flight events, close broker
        connections, and cancel any background tasks before returning.
        After this method returns no further events will be delivered.
        """
        ...
