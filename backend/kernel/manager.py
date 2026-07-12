"""Kernel lifecycle manager.

Coordinates the initialization, configuration, and shutdown of
the AI kernel and all its subsystems. Acts as the composition
root for dependency injection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from kernel.kernel import AIKernel, KernelConfig
from kernel.lifecycle import ComponentInfo, Lifecycle
from kernel.registry import Provider
from kernel.state import KernelState, KernelStatus


@dataclass
class ManagerConfig:
    """Configuration for the kernel manager.

    Attributes:
        kernel_config: Configuration for the AI kernel.
        auto_start: Whether to start the kernel on initialization.
        health_check_interval_seconds: Interval for health monitoring.
        max_startup_time_seconds: Maximum time for kernel startup.
        graceful_shutdown_timeout: Maximum time for graceful shutdown.
        metadata: Additional manager configuration.
    """

    kernel_config: KernelConfig = field(default_factory=KernelConfig)
    auto_start: bool = True
    health_check_interval_seconds: int = 30
    max_startup_time_seconds: int = 60
    graceful_shutdown_timeout: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)


class KernelManager(ABC):
    """Abstract interface for kernel lifecycle management.

    The KernelManager is responsible for:
    - Creating and configuring the kernel instance
    - Managing startup and shutdown sequences
    - Coordinating provider registration
    - Monitoring kernel health
    - Handling recovery from failures
    """

    @property
    @abstractmethod
    def kernel(self) -> AIKernel | None:
        """Get the managed kernel instance.

        Returns:
            The AIKernel instance, or None if not initialized.
        """
        ...

    @property
    @abstractmethod
    def config(self) -> ManagerConfig:
        """Get the manager configuration."""
        ...

    @abstractmethod
    async def initialize(self, config: ManagerConfig | None = None) -> None:
        """Initialize the kernel manager and create the kernel.

        Sets up all kernel subsystems and prepares the kernel
        for operation.

        Args:
            config: Optional configuration override.

        Raises:
            RuntimeError: If initialization fails.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the kernel and begin accepting requests.

        Transitions the kernel from initialized to running state.

        Raises:
            RuntimeError: If the kernel is not initialized.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the kernel gracefully.

        Completes in-progress work and releases resources.
        """
        ...

    @abstractmethod
    async def restart(self) -> None:
        """Restart the kernel.

        Performs a graceful stop followed by a fresh start.
        """
        ...

    @abstractmethod
    async def get_status(self) -> KernelStatus:
        """Get the current kernel operational status.

        Returns:
            Current KernelStatus.
        """
        ...

    @abstractmethod
    async def get_state(self) -> KernelState:
        """Get the full kernel state snapshot.

        Returns:
            Current KernelState.
        """
        ...

    @abstractmethod
    async def register_provider(self, provider: Provider) -> str:
        """Register a provider with the kernel.

        Args:
            provider: The provider to register.

        Returns:
            The provider_id of the registered provider.
        """
        ...

    @abstractmethod
    async def unregister_provider(self, provider_id: str) -> bool:
        """Unregister a provider from the kernel.

        Args:
            provider_id: The provider to remove.

        Returns:
            True if the provider was removed.
        """
        ...

    @abstractmethod
    async def register_component(self, component: Lifecycle) -> None:
        """Register a lifecycle-managed component.

        Args:
            component: The component to manage.
        """
        ...

    @abstractmethod
    async def get_components(self) -> list[ComponentInfo]:
        """Get information about all managed components.

        Returns:
            List of ComponentInfo for registered components.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run a comprehensive health check.

        Checks kernel status, all providers, and all components.

        Returns:
            Health check results with details.
        """
        ...
