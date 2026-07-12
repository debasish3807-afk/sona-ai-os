"""Memory store factory for creating instances.

This module defines the factory framework for creating and configuring
memory store instances. The factory pattern enables centralized
instantiation with consistent configuration and dependency injection.

Classes:
    MemoryFactory: Abstract interface for memory store creation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from .base import MemoryStore
from .types import MemoryType


class MemoryFactory(ABC):
    """Abstract interface for memory store creation.

    The factory manages registration of store implementation classes
    and their default configurations, enabling on-demand instantiation
    of properly configured memory stores.

    Implementations handle dependency resolution, configuration merging,
    and initialization sequencing for new store instances.
    """

    @abstractmethod
    def register_class(
        self,
        memory_type: MemoryType,
        store_class: Type[MemoryStore],
        default_config: Optional[dict[str, Any]] = None,
    ) -> None:
        """Register a memory store class for a specific memory type.

        Associates a concrete MemoryStore implementation class with
        a memory type, along with its default configuration.

        Args:
            memory_type: The memory type this class implements.
            store_class: The concrete class to instantiate.
            default_config: Optional default configuration dictionary.
        """
        ...

    @abstractmethod
    def unregister_class(self, memory_type: MemoryType) -> bool:
        """Unregister a memory store class for a memory type.

        Args:
            memory_type: The memory type to unregister.

        Returns:
            True if a class was found and unregistered, False otherwise.
        """
        ...

    @abstractmethod
    def create(
        self,
        memory_type: MemoryType,
        config: Optional[dict[str, Any]] = None,
    ) -> MemoryStore:
        """Create a memory store instance for the specified type.

        Instantiates the registered class with the provided configuration
        merged over the default configuration.

        Args:
            memory_type: The memory type to create a store for.
            config: Optional configuration overrides.

        Returns:
            A new memory store instance.

        Raises:
            ValueError: If no class is registered for the memory type.
        """
        ...

    @abstractmethod
    def create_all(
        self, configs: Optional[dict[MemoryType, dict[str, Any]]] = None
    ) -> dict[MemoryType, MemoryStore]:
        """Create store instances for all registered memory types.

        Args:
            configs: Optional per-type configuration overrides.

        Returns:
            Mapping of memory type to newly created store instance.
        """
        ...

    @abstractmethod
    def get_registered_types(self) -> list[MemoryType]:
        """Get all memory types that have registered store classes.

        Returns:
            List of memory types with registered implementations.
        """
        ...

    @abstractmethod
    def is_registered(self, memory_type: MemoryType) -> bool:
        """Check if a memory type has a registered store class.

        Args:
            memory_type: The memory type to check.

        Returns:
            True if a class is registered for this type.
        """
        ...
