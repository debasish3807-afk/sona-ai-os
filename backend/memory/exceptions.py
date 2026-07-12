"""Memory-specific exception hierarchy.

This module defines the complete exception hierarchy for the memory engine.
All exceptions inherit from the base MemoryError class and provide structured
error information including error codes, detail dictionaries, and retry hints.

Exception Hierarchy:
    MemoryError (base)
    ├── MemoryNotFoundError - Entry lookup failures
    ├── MemoryStorageError - Write/persist failures
    ├── MemoryRetrievalError - Read/search failures
    ├── MemoryCapacityError - Storage limit exceeded
    ├── MemoryExpirationError - TTL/expiry processing errors
    ├── MemoryConsolidationError - Consolidation process failures
    ├── MemoryIndexError - Index operation failures
    ├── MemoryImportExportError - Import/export operation failures
    └── MemoryPolicyViolation - Policy rule violations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class MemoryError(Exception):
    """Base exception for all memory engine errors.

    All memory-specific exceptions inherit from this class, providing
    a consistent interface for error handling across the memory system.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code for programmatic handling.
        details: Additional structured context about the error.
        retryable: Whether the operation that caused this error can be retried.
    """

    message: str
    error_code: str = "MEMORY_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        """Initialize the Exception base class with the message."""
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.details:
            parts.append(f" details={self.details}")
        if self.retryable:
            parts.append(" (retryable)")
        return "".join(parts)

    def __repr__(self) -> str:
        """Return a detailed repr for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r}, "
            f"retryable={self.retryable!r})"
        )


@dataclass(slots=True)
class MemoryNotFoundError(MemoryError):
    """Raised when a requested memory entry cannot be found.

    This exception is raised during get, update, or delete operations
    when the specified entry_id does not correspond to any stored memory.

    Attributes:
        entry_id: The ID of the memory entry that was not found.
    """

    message: str = "Memory entry not found"
    error_code: str = "MEMORY_NOT_FOUND"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with entry_id in details if provided."""
        if self.entry_id and "entry_id" not in self.details:
            self.details["entry_id"] = self.entry_id
        super().__post_init__()


@dataclass(slots=True)
class MemoryStorageError(MemoryError):
    """Raised when a memory storage operation fails.

    This covers failures during write operations such as store, update,
    or import. Common causes include backend unavailability, serialization
    failures, or constraint violations.

    Attributes:
        operation: The storage operation that failed (e.g., 'store', 'update').
    """

    message: str = "Memory storage operation failed"
    error_code: str = "MEMORY_STORAGE_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    operation: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with operation in details if provided."""
        if self.operation and "operation" not in self.details:
            self.details["operation"] = self.operation
        super().__post_init__()


@dataclass(slots=True)
class MemoryRetrievalError(MemoryError):
    """Raised when a memory retrieval or search operation fails.

    This covers failures during read operations such as get, search,
    or list. Common causes include index corruption, query parsing
    failures, or backend connectivity issues.

    Attributes:
        query: The query or parameters that triggered the failure.
    """

    message: str = "Memory retrieval operation failed"
    error_code: str = "MEMORY_RETRIEVAL_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    query: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with query in details if provided."""
        if self.query and "query" not in self.details:
            self.details["query"] = self.query
        super().__post_init__()


@dataclass(slots=True)
class MemoryCapacityError(MemoryError):
    """Raised when memory storage capacity limits are exceeded.

    This exception indicates that the memory system has reached its
    configured capacity and cannot accept new entries without eviction
    or cleanup.

    Attributes:
        current_usage: Current usage count or bytes.
        max_capacity: Maximum configured capacity.
        scope: The scope in which capacity was exceeded.
    """

    message: str = "Memory capacity limit exceeded"
    error_code: str = "MEMORY_CAPACITY_EXCEEDED"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    current_usage: Optional[int] = None
    max_capacity: Optional[int] = None
    scope: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with capacity details."""
        if self.current_usage is not None:
            self.details.setdefault("current_usage", self.current_usage)
        if self.max_capacity is not None:
            self.details.setdefault("max_capacity", self.max_capacity)
        if self.scope:
            self.details.setdefault("scope", self.scope)
        super().__post_init__()


@dataclass(slots=True)
class MemoryExpirationError(MemoryError):
    """Raised when memory expiration processing encounters an error.

    This covers failures during expiration checks, cleanup of expired
    entries, or TTL enforcement operations.

    Attributes:
        entry_id: The ID of the entry involved in the expiration error.
    """

    message: str = "Memory expiration processing failed"
    error_code: str = "MEMORY_EXPIRATION_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with entry_id in details if provided."""
        if self.entry_id and "entry_id" not in self.details:
            self.details["entry_id"] = self.entry_id
        super().__post_init__()


@dataclass(slots=True)
class MemoryConsolidationError(MemoryError):
    """Raised when memory consolidation processing fails.

    Consolidation involves merging, summarizing, or archiving older
    memories. This exception indicates a failure in that process.

    Attributes:
        task_id: The consolidation task ID that failed.
        entries_affected: Number of entries involved in the failed consolidation.
    """

    message: str = "Memory consolidation failed"
    error_code: str = "MEMORY_CONSOLIDATION_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    task_id: Optional[str] = None
    entries_affected: Optional[int] = None

    def __post_init__(self) -> None:
        """Initialize with consolidation details."""
        if self.task_id:
            self.details.setdefault("task_id", self.task_id)
        if self.entries_affected is not None:
            self.details.setdefault("entries_affected", self.entries_affected)
        super().__post_init__()


@dataclass(slots=True)
class MemoryIndexError(MemoryError):
    """Raised when a memory index operation fails.

    This covers failures during index add, remove, rebuild, or search
    operations. Common causes include corrupted index state or
    incompatible embedding dimensions.

    Attributes:
        index_type: The type of index that encountered the error.
        operation: The index operation that failed.
    """

    message: str = "Memory index operation failed"
    error_code: str = "MEMORY_INDEX_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    index_type: Optional[str] = None
    operation: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with index details."""
        if self.index_type:
            self.details.setdefault("index_type", self.index_type)
        if self.operation:
            self.details.setdefault("operation", self.operation)
        super().__post_init__()


@dataclass(slots=True)
class MemoryImportExportError(MemoryError):
    """Raised when a memory import or export operation fails.

    This covers failures during bulk data transfer operations including
    serialization errors, format incompatibilities, or partial failures.

    Attributes:
        operation: The operation type ('import' or 'export').
        entries_processed: Number of entries successfully processed before failure.
        total_entries: Total number of entries in the operation.
    """

    message: str = "Memory import/export operation failed"
    error_code: str = "MEMORY_IMPORT_EXPORT_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    operation: Optional[str] = None
    entries_processed: Optional[int] = None
    total_entries: Optional[int] = None

    def __post_init__(self) -> None:
        """Initialize with import/export details."""
        if self.operation:
            self.details.setdefault("operation", self.operation)
        if self.entries_processed is not None:
            self.details.setdefault("entries_processed", self.entries_processed)
        if self.total_entries is not None:
            self.details.setdefault("total_entries", self.total_entries)
        super().__post_init__()


@dataclass(slots=True)
class MemoryPolicyViolation(MemoryError):
    """Raised when a memory operation violates a configured policy.

    Policies govern retention, capacity, consolidation, and pinning rules.
    This exception indicates an attempt to perform an action that conflicts
    with an active policy.

    Attributes:
        policy_id: The ID of the policy that was violated.
        policy_name: Human-readable name of the violated policy.
        violation_type: The category of policy violation.
    """

    message: str = "Memory policy violation"
    error_code: str = "MEMORY_POLICY_VIOLATION"
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    violation_type: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize with policy violation details."""
        if self.policy_id:
            self.details.setdefault("policy_id", self.policy_id)
        if self.policy_name:
            self.details.setdefault("policy_name", self.policy_name)
        if self.violation_type:
            self.details.setdefault("violation_type", self.violation_type)
        super().__post_init__()
