"""Memory store registration and discovery.

This module defines the registry framework for managing memory store
instances. The registry enables dynamic registration, discovery, and
lifecycle management of memory store backends.

Classes:
    MemoryStoreEntry: Registration metadata for a memory store instance.
    MemoryRegistry: Abstract interface for memory store registration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .base import MemoryStore
from .types import MemoryType


@dataclass(slots=True)
class MemoryStoreEntry:
    """Registration metadata for a memory store instance.

    Wraps a MemoryStore implementation with registration metadata
    including type mapping, priority, and operational status.

    Attributes:
        store: The memory store instance.
        memory_type: The memory type this store serves.
        registered_at: UTC timestamp when this store was registered.
        enabled: Whether this store is currently active.
        priority: Priority for this store (lower = preferred, used for fallback).
        metadata: Additional registration metadata.
    """

    store: MemoryStore
    memory_type: MemoryType
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryRegistry(ABC):
    """Abstract interface for memory store registration and discovery.

    The registry serves as the service locator for memory stores,
    enabling components to find the appropriate store for a given
    memory type without hard-coding dependencies.
    """

    @abstractmethod
    async def register(
        self,
        memory_type: MemoryType,
        store: MemoryStore,
        priority: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Register a memory store for a specific memory type.

        Args:
            memory_type: The memory type this store will serve.
            store: The memory store instance to register.
            priority: Priority for this store (lower = preferred).
            metadata: Optional registration metadata.
        """
        ...

    @abstractmethod
    async def unregister(self, memory_type: MemoryType) -> bool:
        """Unregister the memory store for a specific type.

        Args:
            memory_type: The memory type to unregister.

        Returns:
            True if a store was found and unregistered, False otherwise.
        """
        ...

    @abstractmethod
    async def get_store(self, memory_type: MemoryType) -> Optional[MemoryStore]:
        """Get the registered memory store for a specific type.

        Args:
            memory_type: The memory type to get the store for.

        Returns:
            The registered store, or None if no store is registered.
        """
        ...

    @abstractmethod
    async def list_stores(self) -> list[MemoryStoreEntry]:
        """List all registered memory stores with their metadata.

        Returns:
            List of all registered store entries.
        """
        ...

    @abstractmethod
    async def get_available_types(self) -> list[MemoryType]:
        """Get all memory types that have registered stores.

        Returns:
            List of memory types with active registrations.
        """
        ...

    @abstractmethod
    async def health_check_all(self) -> dict[MemoryType, bool]:
        """Run health checks on all registered stores.

        Returns:
            Mapping of memory type to health status (True = healthy).
        """
        ...
