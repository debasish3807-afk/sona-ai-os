"""Sona AI OS Event Bus - Internal event/message bus for service communication.

This package provides abstract interfaces for event publishing and subscription,
enabling loosely-coupled communication between services through typed domain events.
Services communicate by publishing DomainEvent instances and subscribing to
specific event types with async handler callbacks.
"""

from sona_events.ports import EventBusPort, EventPublisherPort, EventSubscriberPort
from sona_events.protocols import AsyncEventHandler, EventHandler

__all__ = [
    "AsyncEventHandler",
    "EventBusPort",
    "EventHandler",
    "EventPublisherPort",
    "EventSubscriberPort",
]
