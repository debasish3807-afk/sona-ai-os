"""Connection pool management for HTTP clients.

Manages shared httpx.AsyncClient instances with configurable connection
pooling, timeouts, and lifecycle management.
"""

from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class PoolConfig:
    """Configuration for HTTP connection pools."""

    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    connect_timeout: float = 5.0
    read_timeout: float = 60.0


class ConnectionPoolManager:
    """Manages HTTP connection pools for infrastructure services.

    Creates and caches httpx.AsyncClient instances per named service,
    ensuring proper resource cleanup on shutdown.
    """

    def __init__(self, config: PoolConfig | None = None) -> None:
        self._config = config or PoolConfig()
        self._clients: dict[str, httpx.AsyncClient] = {}

    def get_client(self, name: str, base_url: str) -> httpx.AsyncClient:
        """Get or create a pooled HTTP client for the given service.

        Clients are cached by name. Subsequent calls with the same name
        return the existing client regardless of base_url changes.
        """
        if name not in self._clients:
            transport = httpx.AsyncHTTPTransport(
                retries=2,
            )
            client = httpx.AsyncClient(
                base_url=base_url,
                transport=transport,
                timeout=httpx.Timeout(
                    connect=self._config.connect_timeout,
                    read=self._config.read_timeout,
                    write=self._config.read_timeout,
                    pool=self._config.connect_timeout,
                ),
            )
            self._clients[name] = client
            logger.info(
                "connection_pool.client_created",
                name=name,
                base_url=base_url,
            )
        return self._clients[name]

    async def close_all(self) -> None:
        """Close all managed HTTP clients and release connections."""
        for name, client in self._clients.items():
            try:
                await client.aclose()
                logger.info("connection_pool.client_closed", name=name)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "connection_pool.close_error",
                    name=name,
                    error=str(exc),
                )
        self._clients.clear()

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all managed connection pools."""
        stats: dict[str, dict[str, int]] = {}
        for name, client in self._clients.items():
            stats[name] = {
                "active": 1 if not client.is_closed else 0,
            }
        return stats
