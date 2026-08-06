"""Unit tests for Event Bus abstract port interfaces.

Tests verify that the abstract port interfaces are correctly defined,
cannot be instantiated directly, and that concrete implementations
work as expected.
"""

from dataclasses import dataclass, field
from typing import Type
from uuid import uuid4

import pytest

from sona_shared.domain.primitives import DomainEvent, EntityId, Timestamp
from sona_events.ports import EventBusPort, EventPublisherPort, EventSubscriberPort
from sona_events.protocols import AsyncEventHandler


# --- Test Event Fixtures ---

@dataclass(frozen=True)
class UserCreatedEvent(DomainEvent):
    """Test domain event representing a user creation."""
    user_id: str = ""


@dataclass(frozen=True)
class OrderPlacedEvent(DomainEvent):
    """Test domain event representing an order placement."""
    order_id: str = ""
    amount: float = 0.0


# --- Minimal Concrete Implementation for Testing ---

class InMemoryEventBus(EventBusPort):
    """A minimal in-memory event bus implementation for testing."""

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[AsyncEventHandler]] = {}

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def publish(self, event: DomainEvent) -> None:
        event_type = type(event)
        for handler_type, handlers in self._handlers.items():
            if isinstance(event, handler_type):
                for handler in handlers:
                    await handler(event)

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)

    def subscribe(self, event_type: Type[DomainEvent], handler: AsyncEventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[DomainEvent], handler: AsyncEventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]

    def get_subscribers(self, event_type: Type[DomainEvent]) -> list[AsyncEventHandler]:
        return list(self._handlers.get(event_type, []))


# --- Tests ---

class TestEventPublisherPort:
    """Tests for EventPublisherPort abstract base class."""

    def test_publisher_port_is_abstract(self) -> None:
        """Verify EventPublisherPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EventPublisherPort()  # type: ignore[abstract]

    def test_publisher_has_publish_method(self) -> None:
        """Verify abstract publish method is defined."""
        assert "publish" in EventPublisherPort.__abstractmethods__

    def test_publisher_has_publish_batch_method(self) -> None:
        """Verify abstract publish_batch method is defined."""
        assert "publish_batch" in EventPublisherPort.__abstractmethods__


class TestEventSubscriberPort:
    """Tests for EventSubscriberPort abstract base class."""

    def test_subscriber_port_is_abstract(self) -> None:
        """Verify EventSubscriberPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EventSubscriberPort()  # type: ignore[abstract]

    def test_subscriber_has_subscribe_method(self) -> None:
        """Verify abstract subscribe method is defined."""
        assert "subscribe" in EventSubscriberPort.__abstractmethods__

    def test_subscriber_has_unsubscribe_method(self) -> None:
        """Verify abstract unsubscribe method is defined."""
        assert "unsubscribe" in EventSubscriberPort.__abstractmethods__

    def test_subscriber_has_get_subscribers_method(self) -> None:
        """Verify abstract get_subscribers method is defined."""
        assert "get_subscribers" in EventSubscriberPort.__abstractmethods__


class TestEventBusPort:
    """Tests for EventBusPort combined abstract base class."""

    def test_event_bus_port_is_abstract(self) -> None:
        """Verify EventBusPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EventBusPort()  # type: ignore[abstract]

    def test_event_bus_extends_both_ports(self) -> None:
        """Verify EventBusPort is a subclass of both publisher and subscriber."""
        assert issubclass(EventBusPort, EventPublisherPort)
        assert issubclass(EventBusPort, EventSubscriberPort)

    def test_event_bus_has_start_method(self) -> None:
        """Verify abstract start lifecycle method is defined."""
        assert "start" in EventBusPort.__abstractmethods__

    def test_event_bus_has_stop_method(self) -> None:
        """Verify abstract stop lifecycle method is defined."""
        assert "stop" in EventBusPort.__abstractmethods__


class TestInMemoryEventBus:
    """Integration tests using the InMemoryEventBus concrete implementation."""

    @pytest.mark.asyncio
    async def test_publish_calls_registered_handler(self) -> None:
        """Verify that publishing an event invokes the registered handler."""
        bus = InMemoryEventBus()
        received_events: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received_events.append(event)

        event = UserCreatedEvent(user_id="user-123")
        bus.subscribe(UserCreatedEvent, handler)
        await bus.publish(event)

        assert len(received_events) == 1
        assert isinstance(received_events[0], UserCreatedEvent)

    @pytest.mark.asyncio
    async def test_publish_to_multiple_handlers(self) -> None:
        """Verify that multiple handlers for the same event type are all called."""
        bus = InMemoryEventBus()
        call_count = 0

        async def handler1(event: DomainEvent) -> None:
            nonlocal call_count
            call_count += 1

        async def handler2(event: DomainEvent) -> None:
            nonlocal call_count
            call_count += 1

        bus.subscribe(UserCreatedEvent, handler1)
        bus.subscribe(UserCreatedEvent, handler2)
        await bus.publish(UserCreatedEvent(user_id="abc"))

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_handler(self) -> None:
        """Verify that unsubscribing prevents handler from receiving future events."""
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(UserCreatedEvent, handler)
        bus.unsubscribe(UserCreatedEvent, handler)
        await bus.publish(UserCreatedEvent(user_id="abc"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler_is_noop(self) -> None:
        """Verify that unsubscribing a non-registered handler does not raise."""
        bus = InMemoryEventBus()

        async def handler(event: DomainEvent) -> None:
            pass

        # Should not raise even though handler was never subscribed
        bus.unsubscribe(UserCreatedEvent, handler)

    @pytest.mark.asyncio
    async def test_publish_batch_delivers_all_events(self) -> None:
        """Verify that batch publishing delivers all events in order."""
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(UserCreatedEvent, handler)
        events = [
            UserCreatedEvent(user_id=f"user-{i}")
            for i in range(5)
        ]
        await bus.publish_batch(events)

        assert len(received) == 5

    @pytest.mark.asyncio
    async def test_different_event_types_are_isolated(self) -> None:
        """Verify that handlers for one event type don't receive other event types."""
        bus = InMemoryEventBus()
        user_events: list[DomainEvent] = []
        order_events: list[DomainEvent] = []

        async def user_handler(event: DomainEvent) -> None:
            user_events.append(event)

        async def order_handler(event: DomainEvent) -> None:
            order_events.append(event)

        bus.subscribe(UserCreatedEvent, user_handler)
        bus.subscribe(OrderPlacedEvent, order_handler)

        await bus.publish(UserCreatedEvent(user_id="u1"))
        await bus.publish(OrderPlacedEvent(order_id="o1", amount=99.99))

        assert len(user_events) == 1
        assert len(order_events) == 1
        assert isinstance(user_events[0], UserCreatedEvent)
        assert isinstance(order_events[0], OrderPlacedEvent)

    def test_get_subscribers_returns_registered_handlers(self) -> None:
        """Verify get_subscribers returns all registered handlers."""
        bus = InMemoryEventBus()

        async def handler1(event: DomainEvent) -> None:
            pass

        async def handler2(event: DomainEvent) -> None:
            pass

        bus.subscribe(UserCreatedEvent, handler1)
        bus.subscribe(UserCreatedEvent, handler2)

        subscribers = bus.get_subscribers(UserCreatedEvent)
        assert len(subscribers) == 2
        assert handler1 in subscribers
        assert handler2 in subscribers

    def test_get_subscribers_returns_empty_for_unsubscribed_type(self) -> None:
        """Verify get_subscribers returns empty list for types with no handlers."""
        bus = InMemoryEventBus()
        subscribers = bus.get_subscribers(UserCreatedEvent)
        assert subscribers == []
