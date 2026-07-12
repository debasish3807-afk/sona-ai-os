"""Memory event definitions.

This module defines the event system for the memory engine. Events are emitted
during memory operations to enable reactive behavior, logging, metrics collection,
and inter-component communication.

The event system follows an observer pattern where components can subscribe to
specific event types and react to memory state changes asynchronously.

Classes:
    MemoryEvents: Constants for all memory event types.
    MemoryEvent: Frozen dataclass representing a single emitted event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


class MemoryEvents:
    """Constants defining all memory event types.

    These constants serve as event type identifiers for the memory event system.
    They are grouped by category:

    Memory Lifecycle Events:
        MEMORY_STORED: A new memory entry has been persisted.
        MEMORY_RETRIEVED: A memory entry has been accessed/read.
        MEMORY_UPDATED: An existing memory entry has been modified.
        MEMORY_DELETED: A memory entry has been permanently removed.
        MEMORY_EXPIRED: A memory entry has reached its expiration time.
        MEMORY_CONSOLIDATED: Memories have been merged/summarized.
        MEMORY_PINNED: A memory entry has been pinned (eviction-exempt).
        MEMORY_UNPINNED: A memory entry has been unpinned.

    Index Events:
        INDEX_UPDATED: An index has been incrementally updated.
        INDEX_REBUILT: An index has been fully rebuilt from scratch.

    Policy and Capacity Events:
        POLICY_APPLIED: A retention/capacity policy has been enforced.
        CAPACITY_WARNING: Memory usage approaching configured limits.
        CAPACITY_EXCEEDED: Memory usage has exceeded configured limits.
    """

    # Memory Lifecycle Events
    MEMORY_STORED: str = "memory.stored"
    MEMORY_RETRIEVED: str = "memory.retrieved"
    MEMORY_UPDATED: str = "memory.updated"
    MEMORY_DELETED: str = "memory.deleted"
    MEMORY_EXPIRED: str = "memory.expired"
    MEMORY_CONSOLIDATED: str = "memory.consolidated"
    MEMORY_PINNED: str = "memory.pinned"
    MEMORY_UNPINNED: str = "memory.unpinned"

    # Index Events
    INDEX_UPDATED: str = "index.updated"
    INDEX_REBUILT: str = "index.rebuilt"

    # Policy and Capacity Events
    POLICY_APPLIED: str = "policy.applied"
    CAPACITY_WARNING: str = "capacity.warning"
    CAPACITY_EXCEEDED: str = "capacity.exceeded"


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    """Represents a single event emitted by the memory system.

    MemoryEvent instances are immutable (frozen) records of state changes
    or significant operations within the memory engine. They carry context
    about what happened, which memory was involved, and any associated data.

    Attributes:
        event_id: Unique identifier for this event instance (UUID4).
        event_type: The type of event, one of MemoryEvents constants.
        memory_id: Optional ID of the memory entry involved in this event.
        memory_type: Optional type classification of the involved memory.
        scope: Optional scope of the involved memory.
        timestamp: UTC timestamp when this event was emitted.
        data: Event-specific payload data (e.g., the stored content, search query).
        metadata: Additional context metadata (e.g., user_id, session_id, source).
    """

    event_type: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_id: Optional[str] = None
    memory_type: Optional[str] = None
    scope: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return a concise string representation of the event."""
        parts = [f"MemoryEvent({self.event_type}"]
        if self.memory_id:
            parts.append(f", memory_id={self.memory_id}")
        if self.memory_type:
            parts.append(f", type={self.memory_type}")
        parts.append(f", ts={self.timestamp.isoformat()})")
        return "".join(parts)
