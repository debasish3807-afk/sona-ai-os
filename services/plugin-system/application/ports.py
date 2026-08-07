"""Abstract port interfaces for the Plugin System service.

Defines the contracts that infrastructure adapters must implement
to provide plugin lifecycle management and registry capabilities.
"""

from abc import ABC, abstractmethod

from domain.models import PluginInstance, PluginManifest


class PluginPort(ABC):
    """Port for individual plugin lifecycle operations.

    Infrastructure adapters implement this port to provide plugin
    activation, deactivation, capability discovery, and health monitoring.
    """

    @abstractmethod
    async def activate(self) -> None:
        """Activate the plugin, making it available for use.

        Raises:
            RuntimeError: If the plugin cannot be activated.
        """
        ...

    @abstractmethod
    async def deactivate(self) -> None:
        """Deactivate the plugin, stopping all its operations.

        Raises:
            RuntimeError: If the plugin cannot be safely deactivated.
        """
        ...

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Retrieve the list of capabilities this plugin provides.

        Returns:
            A list of capability identifiers exposed by this plugin.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the plugin is healthy and functioning correctly.

        Returns:
            True if the plugin is healthy, False otherwise.
        """
        ...


class PluginRegistryPort(ABC):
    """Port for plugin registry and lifecycle management.

    Infrastructure adapters implement this port to provide plugin
    installation, uninstallation, activation, deactivation, and
    listing capabilities across the entire plugin ecosystem.
    """

    @abstractmethod
    async def install(self, manifest: PluginManifest) -> str:
        """Install a plugin from its manifest definition.

        Args:
            manifest: The plugin manifest describing the plugin to install.

        Returns:
            The plugin_id of the successfully installed plugin.

        Raises:
            ValueError: If the manifest is invalid or the plugin already exists.
        """
        ...

    @abstractmethod
    async def uninstall(self, plugin_id: str) -> bool:
        """Uninstall a plugin by its identifier.

        Args:
            plugin_id: The unique identifier of the plugin to uninstall.

        Returns:
            True if the plugin was successfully uninstalled, False if not found.
        """
        ...

    @abstractmethod
    async def activate(self, plugin_id: str) -> bool:
        """Activate an installed plugin.

        Args:
            plugin_id: The unique identifier of the plugin to activate.

        Returns:
            True if the plugin was successfully activated, False otherwise.
        """
        ...

    @abstractmethod
    async def deactivate(self, plugin_id: str) -> bool:
        """Deactivate an active plugin.

        Args:
            plugin_id: The unique identifier of the plugin to deactivate.

        Returns:
            True if the plugin was successfully deactivated, False otherwise.
        """
        ...

    @abstractmethod
    async def list_plugins(self) -> list[PluginInstance]:
        """List all installed plugins with their current status.

        Returns:
            A list of PluginInstance objects representing all installed plugins.
        """
        ...
