"""Memory system metrics and observability.

This module defines the metrics collection framework for the memory engine.
It provides structured tracking of operation counts, latencies, error rates,
and resource utilization for monitoring and debugging.

Classes:
    MemoryOperation: Enumeration of trackable memory operations.
    OperationMetric: Metrics for a specific operation type.
    MemoryMetrics: Complete metrics snapshot for the memory system.
    MetricsCollector: Abstract interface for metrics collection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class MemoryOperation(str, Enum):
    """Enumeration of trackable memory operations.

    Each enum value represents a distinct operation category
    for which metrics are collected independently.

    Attributes:
        STORE: Memory write/persist operations.
        RETRIEVE: Single entry retrieval operations.
        UPDATE: Memory modification operations.
        DELETE: Memory removal operations.
        SEARCH: Search/query operations.
        CONSOLIDATE: Memory consolidation operations.
        INDEX: Index maintenance operations.
    """

    STORE = "store"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    CONSOLIDATE = "consolidate"
    INDEX = "index"


@dataclass(slots=True)
class OperationMetric:
    """Metrics for a specific operation type.

    Tracks count, timing distribution, and error rate for a single
    category of memory operation.

    Attributes:
        operation: The operation type these metrics describe.
        count: Total number of completed operations.
        total_ms: Total cumulative time for all operations in milliseconds.
        avg_ms: Average operation time in milliseconds.
        p95_ms: 95th percentile operation time in milliseconds.
        p99_ms: 99th percentile operation time in milliseconds.
        min_ms: Minimum observed operation time in milliseconds.
        max_ms: Maximum observed operation time in milliseconds.
        error_count: Total number of failed operations.
        last_operation: UTC timestamp of the most recent operation.
        last_error: UTC timestamp of the most recent error (None if no errors).
    """

    operation: MemoryOperation
    count: int = 0
    total_ms: float = 0.0
    avg_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    error_count: int = 0
    last_operation: Optional[datetime] = None
    last_error: Optional[datetime] = None


@dataclass(slots=True)
class MemoryMetrics:
    """Complete metrics snapshot for the memory system.

    Aggregates per-operation metrics with system-wide resource
    utilization and cache performance data.

    Attributes:
        operations: Per-operation-type metrics.
        cache_hits: Total number of cache hits across all operations.
        cache_misses: Total number of cache misses.
        cache_hit_ratio: Computed cache hit ratio (0.0-1.0).
        total_entries: Total memory entries currently stored.
        memory_usage_bytes: Estimated total memory usage in bytes.
        uptime_seconds: Seconds since the metrics collector was initialized.
        started_at: UTC timestamp when metrics collection started.
        last_reset: UTC timestamp of the last metrics reset (None if never reset).
        metadata: Additional system-specific metrics.
    """

    operations: dict[MemoryOperation, OperationMetric] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_ratio: float = 0.0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    uptime_seconds: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_reset: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsCollector(ABC):
    """Abstract interface for memory system metrics collection.

    Implementations handle recording, aggregation, and export of
    operational metrics. They may persist metrics in-memory, to a
    time-series database, or to an external monitoring service.
    """

    @abstractmethod
    async def record_operation(
        self,
        operation: MemoryOperation,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a completed operation with timing information.

        Args:
            operation: The type of operation that was performed.
            duration_ms: Time taken for the operation in milliseconds.
            success: Whether the operation completed without error.
            metadata: Optional additional context about the operation.
        """
        ...

    @abstractmethod
    async def get_metrics(self) -> MemoryMetrics:
        """Get the current metrics snapshot.

        Returns:
            Complete metrics snapshot covering all tracked operations.
        """
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Reset all metrics to zero.

        Records the reset timestamp and clears all accumulated metrics.
        """
        ...

    @abstractmethod
    async def export(self, format: str = "dict") -> dict[str, Any]:
        """Export metrics in a specified format.

        Args:
            format: Export format ('dict', 'prometheus', 'json').

        Returns:
            Metrics data in the requested format as a dictionary.
        """
        ...
