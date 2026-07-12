"""Component lifecycle management.

Defines lifecycle interfaces and states for kernel components.
Ensures proper initialization, health checking, and graceful
shutdown of all managed components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ComponentState(str, Enum):
    """Lifecycle state of a managed component."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class HealthStatus(str, Enum):
    """Health status of a component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health check result for a component.

    Attributes:
        status: Current health status.
        message: Human-readable status message.
        details: Additional health check details.
        last_check: Timestamp of the last health check.
        consecutive_failures: Number of consecutive health check failures.
    """

    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0

    @property
    def is_healthy(self) -> bool:
        """Check if the component is healthy."""
        return self.status == HealthStatus.HEALTHY


@dataclass
class ComponentInfo:
    """Metadata about a managed component.

    Attributes:
        name: Human-readable component name.
        component_id: Unique identifier.
        version: Component version string.
        state: Current lifecycle state.
        health: Latest health check result.
        started_at: Timestamp when component entered RUNNING state.
        metadata: Additional component metadata.
        dependencies: List of component IDs this component depends on.
    """

    name: str
    component_id: str
    version: str = "0.0.0"
    state: ComponentState = ComponentState.UNINITIALIZED
    health: ComponentHealth = field(default_factory=ComponentHealth)
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class Lifecycle(ABC):
    """Abstract lifecycle interface for managed components.

    All kernel components that require initialization, health monitoring,
    and graceful shutdown should implement this interface.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        Perform any setup required before the component can accept work.
        This may include establishing connections, loading configuration,
        or validating prerequisites.

        Raises:
            RuntimeError: If initialization fails.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the component.

        Transition from initialized to running state. Begin accepting
        and processing work.

        Raises:
            RuntimeError: If the component cannot start.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component gracefully.

        Complete in-progress work, release resources, and transition
        to stopped state. Should be idempotent.
        """
        ...

    @abstractmethod
    async def health_check(self) -> ComponentHealth:
        """Perform a health check on the component.

        Returns:
            ComponentHealth with current status and details.
        """
        ...

    @abstractmethod
    def get_info(self) -> ComponentInfo:
        """Get component information and metadata.

        Returns:
            ComponentInfo with current state and details.
        """
        ...


class LifecycleManager(ABC):
    """Abstract manager for coordinating component lifecycles.

    Manages initialization order (respecting dependencies),
    health monitoring, and coordinated shutdown.
    """

    @abstractmethod
    async def register(self, component: Lifecycle) -> None:
        """Register a component for lifecycle management.

        Args:
            component: Component implementing the Lifecycle interface.

        Raises:
            ValueError: If a component with the same ID is already registered.
        """
        ...

    @abstractmethod
    async def unregister(self, component_id: str) -> bool:
        """Unregister a component from lifecycle management.

        The component will be stopped before removal if currently running.

        Args:
            component_id: ID of the component to remove.

        Returns:
            True if the component was found and unregistered.
        """
        ...

    @abstractmethod
    async def start_all(self) -> Dict[str, ComponentState]:
        """Start all registered components respecting dependency order.

        Returns:
            Mapping of component IDs to their resulting states.
        """
        ...

    @abstractmethod
    async def stop_all(self) -> Dict[str, ComponentState]:
        """Stop all registered components in reverse dependency order.

        Returns:
            Mapping of component IDs to their resulting states.
        """
        ...

    @abstractmethod
    async def health_check_all(self) -> Dict[str, ComponentHealth]:
        """Run health checks on all registered components.

        Returns:
            Mapping of component IDs to their health status.
        """
        ...

    @abstractmethod
    def get_component(self, component_id: str) -> Optional[Lifecycle]:
        """Get a registered component by ID.

        Args:
            component_id: The component identifier.

        Returns:
            The component instance or None if not found.
        """
        ...

    @abstractmethod
    def get_all_components(self) -> List[ComponentInfo]:
        """Get information about all registered components.

        Returns:
            List of ComponentInfo for all managed components.
        """
        ...

    @abstractmethod
    def get_state(self, component_id: str) -> Optional[ComponentState]:
        """Get the current state of a component.

        Args:
            component_id: The component identifier.

        Returns:
            Current ComponentState or None if not found.
        """
        ...
