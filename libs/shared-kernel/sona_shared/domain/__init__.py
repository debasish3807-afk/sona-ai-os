"""Domain primitives for the Sona AI OS shared kernel.

Exports all public domain types: EntityId, Timestamp, Entity, DomainEvent, Result.
"""

from sona_shared.domain.primitives import (
    DomainEvent,
    Entity,
    EntityId,
    Result,
    Timestamp,
)

__all__ = [
    "DomainEvent",
    "Entity",
    "EntityId",
    "Result",
    "Timestamp",
]
