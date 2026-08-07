"""Resource manager for MCP Integration.

Manages MCP resources (files, data) exposed by servers.
Provides listing, reading, and metadata caching.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class MCPResource:
    """Represents a resource exposed by an MCP server.

    Attributes:
        uri: Unique resource URI (e.g., 'file:///path/to/file').
        name: Human-readable name.
        description: Description of the resource.
        mime_type: MIME type of the resource content.
        server_id: ID of the server exposing this resource.
    """

    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    server_id: str = ""


@dataclass
class ResourceContent:
    """Content retrieved from an MCP resource.

    Attributes:
        uri: The resource URI.
        content: The raw content data.
        mime_type: MIME type of the content.
        metadata: Additional metadata about the resource.
    """

    uri: str
    content: str
    mime_type: str = "text/plain"
    metadata: dict[str, Any] = field(default_factory=dict)


class ResourceManager:
    """Manages MCP resources with listing, reading, and caching.

    Provides a centralized view of resources available across
    all connected MCP servers.
    """

    def __init__(self) -> None:
        """Initialize the resource manager."""
        self._resources: dict[str, MCPResource] = {}
        self._content_cache: dict[str, ResourceContent] = {}
        self._server_resources: dict[str, set[str]] = {}

    async def register_resource(self, resource: MCPResource) -> None:
        """Register a resource in the manager.

        Args:
            resource: The MCPResource to register.
        """
        self._resources[resource.uri] = resource
        if resource.server_id not in self._server_resources:
            self._server_resources[resource.server_id] = set()
        self._server_resources[resource.server_id].add(resource.uri)
        await logger.ainfo(
            "resource_registered",
            uri=resource.uri,
            name=resource.name,
            server_id=resource.server_id,
        )

    async def unregister_resource(self, uri: str) -> bool:
        """Remove a resource from the manager.

        Args:
            uri: The resource URI to remove.

        Returns:
            True if removed, False if not found.
        """
        resource = self._resources.pop(uri, None)
        if resource is None:
            return False
        self._content_cache.pop(uri, None)
        if resource.server_id in self._server_resources:
            self._server_resources[resource.server_id].discard(uri)
        return True

    async def get_resource(self, uri: str) -> MCPResource | None:
        """Get a resource by its URI.

        Args:
            uri: The resource URI.

        Returns:
            The MCPResource if found, None otherwise.
        """
        return self._resources.get(uri)

    async def list_resources(self, server_id: str | None = None) -> list[MCPResource]:
        """List all resources, optionally filtered by server.

        Args:
            server_id: Optional server to filter by.

        Returns:
            A list of MCPResource instances.
        """
        if server_id is not None:
            uris = self._server_resources.get(server_id, set())
            return [self._resources[uri] for uri in uris if uri in self._resources]
        return list(self._resources.values())

    async def read_resource(self, uri: str) -> ResourceContent | None:
        """Read resource content (from cache if available).

        Args:
            uri: The resource URI to read.

        Returns:
            The ResourceContent if available, None if not found.
        """
        # Check cache
        if uri in self._content_cache:
            return self._content_cache[uri]

        resource = self._resources.get(uri)
        if resource is None:
            return None

        # Simulated read — in production, this would call the server
        content = ResourceContent(
            uri=uri,
            content=f"Content of {resource.name}",
            mime_type=resource.mime_type,
        )
        self._content_cache[uri] = content
        return content

    async def cache_content(self, uri: str, content: ResourceContent) -> None:
        """Manually cache content for a resource.

        Args:
            uri: The resource URI.
            content: The content to cache.
        """
        self._content_cache[uri] = content

    async def invalidate_cache(self, uri: str | None = None) -> None:
        """Invalidate cached content.

        Args:
            uri: Specific URI to invalidate, or None for all.
        """
        if uri is not None:
            self._content_cache.pop(uri, None)
        else:
            self._content_cache.clear()

    async def remove_server_resources(self, server_id: str) -> int:
        """Remove all resources for a server.

        Args:
            server_id: The server whose resources to remove.

        Returns:
            Number of resources removed.
        """
        uris = self._server_resources.pop(server_id, set())
        for uri in uris:
            self._resources.pop(uri, None)
            self._content_cache.pop(uri, None)
        return len(uris)

    @property
    def resource_count(self) -> int:
        """Return total number of registered resources."""
        return len(self._resources)

    @property
    def cache_size(self) -> int:
        """Return number of cached resource contents."""
        return len(self._content_cache)
