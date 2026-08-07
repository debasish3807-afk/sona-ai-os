"""Connection pool optimization for httpx clients."""

from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class PoolConfig:
    """Configuration for connection pool behavior.

    Attributes:
        max_connections: Maximum total connections in the pool.
        max_keepalive_connections: Maximum idle connections to keep alive.
        keepalive_expiry: Seconds before idle connections are closed.
        connect_timeout: Timeout for establishing a connection in seconds.
        read_timeout: Timeout for reading response data in seconds.
        write_timeout: Timeout for writing request data in seconds.
    """

    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    connect_timeout: float = 5.0
    read_timeout: float = 60.0
    write_timeout: float = 10.0


class ConnectionPoolManager:
    """Manages optimized httpx connection pools per provider.

    Creates and caches httpx.AsyncClient instances with connection
    pooling configured for each provider's base URL.
    """

    def __init__(self, default_config: PoolConfig | None = None) -> None:
        """Initialize the connection pool manager.

        Args:
            default_config: Default pool configuration. Uses defaults if None.
        """
        self._pools: dict[str, httpx.AsyncClient] = {}
        self._config = default_config or PoolConfig()

    def get_client(self, provider: str, base_url: str) -> httpx.AsyncClient:
        """Get or create an httpx client for a provider.

        Reuses existing clients for the same provider. Creates a new
        client with optimized connection pool settings if one doesn't exist.

        Args:
            provider: The provider name (used as cache key).
            base_url: The base URL for the provider's API.

        Returns:
            An httpx.AsyncClient configured for the provider.
        """
        if provider not in self._pools:
            limits = httpx.Limits(
                max_connections=self._config.max_connections,
                max_keepalive_connections=self._config.max_keepalive_connections,
                keepalive_expiry=self._config.keepalive_expiry,
            )
            timeout = httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.read_timeout,
                write=self._config.write_timeout,
                pool=self._config.connect_timeout,
            )
            client = httpx.AsyncClient(
                base_url=base_url,
                limits=limits,
                timeout=timeout,
            )
            self._pools[provider] = client
            logger.info(
                "connection_pool_created",
                provider=provider,
                base_url=base_url,
                max_connections=self._config.max_connections,
            )
        return self._pools[provider]

    async def close_all(self) -> None:
        """Close all managed connection pools.

        Iterates through all cached clients and closes them gracefully.
        """
        for provider, client in self._pools.items():
            await client.aclose()
            logger.info("connection_pool_closed", provider=provider)
        self._pools.clear()

    async def close(self, provider: str) -> None:
        """Close the connection pool for a specific provider.

        Args:
            provider: The provider whose pool to close.
        """
        client = self._pools.pop(provider, None)
        if client:
            await client.aclose()
            logger.info("connection_pool_closed", provider=provider)

    def get_pool_stats(self) -> dict[str, dict[str, int]]:
        """Get connection pool statistics for all providers.

        Returns:
            Dictionary mapping provider names to their pool stats.
        """
        stats: dict[str, dict[str, int]] = {}
        for provider, client in self._pools.items():
            pool = client._transport  # noqa: SLF001
            if isinstance(pool, httpx.AsyncHTTPTransport):
                stats[provider] = {
                    "max_connections": self._config.max_connections,
                    "max_keepalive": self._config.max_keepalive_connections,
                }
            else:
                stats[provider] = {
                    "max_connections": self._config.max_connections,
                    "max_keepalive": self._config.max_keepalive_connections,
                }
        return stats
