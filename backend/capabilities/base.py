"""Base Capability — abstract contract for all capability implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from capabilities.schemas import CapabilityState


class BaseCapability(ABC):
    """Abstract base class for all capability implementations.

    Every concrete capability in the fabric implements this protocol.
    The manager coordinates capabilities through this interface.
    """

    @property
    @abstractmethod
    def capability_id(self) -> str:
        """Unique identifier for this capability instance."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the capability."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string."""
        ...

    @property
    @abstractmethod
    def state(self) -> CapabilityState:
        """Current lifecycle state."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the capability (load resources, establish connections)."""
        ...

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the capability with the given context.

        Args:
            context: Execution context containing parameters and state.

        Returns:
            Result dictionary with execution output.
        """
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the capability is healthy and operational."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the capability and release resources."""
        ...

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Return metadata about this capability."""
        ...
