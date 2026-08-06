"""Sona AI OS Shared Kernel - Domain primitives and common interfaces.

This package provides the foundational types shared across all services
in the Sona AI OS monorepo, including value objects, base entities,
domain events, and the Result pattern for error handling.
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
