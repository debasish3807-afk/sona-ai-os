"""Memory OS domain events."""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class MemoryStoredEvent(DomainEvent):
    """Emitted when a memory entry is stored."""

    user_id: str = ""
    memory_id: str = ""
    memory_type: str = ""
    importance: float = 0.0


@dataclass(frozen=True)
class MemoryRetrievedEvent(DomainEvent):
    """Emitted when memories are retrieved by a query."""

    user_id: str = ""
    query: str = ""
    results_count: int = 0


@dataclass(frozen=True)
class MemoryConsolidatedEvent(DomainEvent):
    """Emitted when memories are consolidated (promoted to long-term)."""

    user_id: str = ""
    consolidated_count: int = 0


@dataclass(frozen=True)
class MemoryForgottenEvent(DomainEvent):
    """Emitted when a memory is explicitly forgotten/deleted."""

    user_id: str = ""
    memory_id: str = ""


@dataclass(frozen=True)
class MemoryExpiredEvent(DomainEvent):
    """Emitted when memories are removed due to TTL expiration."""

    user_id: str = ""
    expired_count: int = 0
