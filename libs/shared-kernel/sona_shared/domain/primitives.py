"""Domain primitives for the Sona AI OS shared kernel.

Provides base value objects, entities, domain events, and the Result pattern
used across all services in the monorepo.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

# --- Value Objects ---


@dataclass(frozen=True)
class EntityId:
    """Immutable unique identifier for all domain entities."""

    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Timestamp:
    """Immutable timestamp value object."""

    value: datetime = field(default_factory=lambda: datetime.now(UTC))


# --- Base Entity ---


@dataclass
class Entity:
    """Base class for all domain entities."""

    id: EntityId = field(default_factory=EntityId)
    created_at: Timestamp = field(default_factory=Timestamp)
    updated_at: Timestamp = field(default_factory=Timestamp)


# --- Domain Events ---


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: EntityId = field(default_factory=EntityId)
    occurred_at: Timestamp = field(default_factory=Timestamp)
    aggregate_id: EntityId | None = None


# --- Result Pattern ---

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Encapsulates success/failure without exceptions.

    Use Result.ok(value) for successful operations and
    Result.fail(error) for failed operations.
    """

    _value: T | None = None
    _error: E | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Create a successful Result containing the given value."""
        return cls(_value=value)

    @classmethod
    def fail(cls, error: E) -> "Result[T, E]":
        """Create a failed Result containing the given error."""
        return cls(_error=error)

    @property
    def is_success(self) -> bool:
        """Return True if this Result represents a success."""
        return self._error is None

    @property
    def value(self) -> T:
        """Access the success value. Raises ValueError if Result is a failure."""
        if self._error is not None:
            raise ValueError("Cannot access value of failed Result")
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> E:
        """Access the error value. Raises ValueError if Result is a success."""
        if self._error is None:
            raise ValueError("Cannot access error of successful Result")
        return self._error
