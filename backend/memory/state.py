"""Memory system state management.

This module defines the state tracking framework for the memory engine.
It provides a consistent view of the system's operational status, health
metrics, and lifecycle information.

Classes:
    MemorySystemStatus: Enumeration of system operational states.
    MemorySystemState: Complete snapshot of the memory system state.
    MemoryStateManager: Abstract interface for state management operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .index import IndexHealth, IndexType
from .types import MemoryStats


class MemorySystemStatus(str, Enum):
    """Enumeration of memory system operational states.

    Represents the overall health and readiness of the memory engine.

    Attributes:
        INITIALIZING: System is starting up and not yet ready.
        READY: System is fully operational and accepting requests.
        DEGRADED: System is operational but with reduced capabilities.
        REBUILDING: System is rebuilding indices or performing maintenance.
        SHUTTING_DOWN: System is in the process of shutting down.
        ERROR: System encountered a critical error and is not operational.
    """

    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    REBUILDING = "rebuilding"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


@dataclass(slots=True)
class MemorySystemState:
    """Complete snapshot of the memory system state.

    Captures the current operational status, statistics, index health,
    policy compliance, and lifecycle timestamps.

    Attributes:
        status: Current operational status of the system.
        stats: Aggregate memory statistics.
        index_health: Health status of each index type.
        policy_violations: List of current policy violation descriptions.
        started_at: UTC timestamp when the system was initialized.
        last_consolidation: UTC timestamp of the last consolidation run.
        last_health_check: UTC timestamp of the last health check.
        error_message: Error description if status is ERROR.
        metadata: Additional state metadata for extensibility.
    """

    status: MemorySystemStatus = MemorySystemStatus.INITIALIZING
    stats: MemoryStats | None = None
    index_health: dict[IndexType, IndexHealth] = field(default_factory=dict)
    policy_violations: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    last_consolidation: datetime | None = None
    last_health_check: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryStateManager(ABC):
    """Abstract interface for memory system state management.

    Provides operations to query, update, and monitor the overall
    state of the memory engine. Implementations maintain the state
    in memory, a database, or distributed state store.
    """

    @abstractmethod
    async def get_state(self) -> MemorySystemState:
        """Get the current system state snapshot.

        Returns:
            A complete snapshot of the current memory system state.
        """
        ...

    @abstractmethod
    async def set_status(
        self, status: MemorySystemStatus, error_message: str | None = None
    ) -> None:
        """Update the system's operational status.

        Args:
            status: The new operational status.
            error_message: Optional error description (for ERROR status).
        """
        ...

    @abstractmethod
    async def update_stats(self, stats: MemoryStats) -> None:
        """Update the aggregate memory statistics.

        Args:
            stats: The new statistics snapshot.
        """
        ...

    @abstractmethod
    async def record_operation(self, operation: str, success: bool, duration_ms: float) -> None:
        """Record a completed operation for state tracking.

        Args:
            operation: The operation type that was performed.
            success: Whether the operation completed successfully.
            duration_ms: Time taken for the operation in milliseconds.
        """
        ...

    @abstractmethod
    async def get_health(self) -> dict[str, Any]:
        """Get a comprehensive health report for the memory system.

        Returns:
            Dictionary containing health information including:
                - status: Current system status string.
                - index_health: Health of each index.
                - uptime_seconds: Seconds since system started.
                - policy_violations: Count of active violations.
                - last_consolidation: Timestamp of last consolidation.
                - degraded_components: List of components with issues.
        """
        ...
