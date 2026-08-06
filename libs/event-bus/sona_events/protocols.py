"""Event handler protocols for the Event Bus library.

Defines typed event handler protocols that receive specific DomainEvent
subtypes, enabling type-safe event subscription and dispatch.
"""

from typing import Awaitable, Callable, Protocol, TypeVar, runtime_checkable

from sona_shared.domain.primitives import DomainEvent

# TypeVar for specific DomainEvent subtypes
E = TypeVar("E", bound=DomainEvent)


@runtime_checkable
class EventHandler(Protocol[E]):
    """Protocol for typed event handlers.

    An event handler is any callable that accepts a DomainEvent subtype
    and returns an awaitable. This allows both functions and classes to
    serve as handlers.

    Example usage::

        async def handle_user_created(event: UserCreatedEvent) -> None:
            await send_welcome_email(event.user_id)

        class OrderProcessor:
            async def __call__(self, event: OrderPlacedEvent) -> None:
                await self.process_order(event.order_id)
    """

    async def __call__(self, event: E) -> None:
        """Handle the incoming domain event.

        Args:
            event: The domain event to handle.
        """
        ...


# Type alias for async event handler functions
AsyncEventHandler = Callable[[DomainEvent], Awaitable[None]]
