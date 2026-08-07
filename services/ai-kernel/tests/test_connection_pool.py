"""Unit tests for the connection pool module.

Tests verify client creation, reuse, cleanup, and stats.
"""

import httpx
import pytest

from sona_ai_kernel.infrastructure.connection_pool import (
    ConnectionPoolManager,
    PoolConfig,
)


class TestPoolConfig:
    """Tests for PoolConfig defaults."""

    def test_default_values(self) -> None:
        """Verify default pool configuration."""
        config = PoolConfig()
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_expiry == 30.0
        assert config.connect_timeout == 5.0
        assert config.read_timeout == 60.0
        assert config.write_timeout == 10.0


class TestConnectionPoolManager:
    """Tests for the ConnectionPoolManager."""

    def test_get_client_creates_new(self) -> None:
        """get_client creates a new client for unknown provider."""
        manager = ConnectionPoolManager()
        client = manager.get_client("openai", "https://api.openai.com")
        assert isinstance(client, httpx.AsyncClient)

    def test_get_client_reuses_existing(self) -> None:
        """get_client returns same client for same provider."""
        manager = ConnectionPoolManager()
        client1 = manager.get_client("openai", "https://api.openai.com")
        client2 = manager.get_client("openai", "https://api.openai.com")
        assert client1 is client2

    def test_different_providers_different_clients(self) -> None:
        """Different providers get different clients."""
        manager = ConnectionPoolManager()
        client1 = manager.get_client("openai", "https://api.openai.com")
        client2 = manager.get_client("anthropic", "https://api.anthropic.com")
        assert client1 is not client2

    @pytest.mark.asyncio
    async def test_close_all(self) -> None:
        """close_all closes and removes all clients."""
        manager = ConnectionPoolManager()
        manager.get_client("openai", "https://api.openai.com")
        manager.get_client("anthropic", "https://api.anthropic.com")

        await manager.close_all()
        # Pool is now empty - next get_client creates new
        stats = manager.get_pool_stats()
        assert stats == {}

    @pytest.mark.asyncio
    async def test_close_single_provider(self) -> None:
        """close() removes only the specified provider's client."""
        manager = ConnectionPoolManager()
        manager.get_client("openai", "https://api.openai.com")
        manager.get_client("anthropic", "https://api.anthropic.com")

        await manager.close("openai")

        stats = manager.get_pool_stats()
        assert "openai" not in stats
        assert "anthropic" in stats

    @pytest.mark.asyncio
    async def test_close_nonexistent_provider(self) -> None:
        """close() for non-existent provider does nothing."""
        manager = ConnectionPoolManager()
        await manager.close("nonexistent")  # Should not raise

    def test_get_pool_stats(self) -> None:
        """get_pool_stats returns info for all pools."""
        config = PoolConfig(max_connections=50, max_keepalive_connections=10)
        manager = ConnectionPoolManager(default_config=config)
        manager.get_client("openai", "https://api.openai.com")

        stats = manager.get_pool_stats()
        assert "openai" in stats
        assert stats["openai"]["max_connections"] == 50
        assert stats["openai"]["max_keepalive"] == 10

    def test_custom_config(self) -> None:
        """Custom pool config is applied to created clients."""
        config = PoolConfig(
            max_connections=50,
            connect_timeout=10.0,
            read_timeout=120.0,
        )
        manager = ConnectionPoolManager(default_config=config)
        client = manager.get_client("test", "http://localhost:8000")
        assert client.timeout.connect == 10.0
        assert client.timeout.read == 120.0

    @pytest.mark.asyncio
    async def test_close_all_then_recreate(self) -> None:
        """After close_all, new clients can be created."""
        manager = ConnectionPoolManager()
        manager.get_client("openai", "https://api.openai.com")

        await manager.close_all()

        # Should create a new client
        client = manager.get_client("openai", "https://api.openai.com")
        assert isinstance(client, httpx.AsyncClient)
