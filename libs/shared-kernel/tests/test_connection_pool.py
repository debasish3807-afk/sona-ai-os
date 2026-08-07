"""Tests for the connection pool manager."""

from sona_shared.infra.connection_pool import ConnectionPoolManager, PoolConfig


class TestPoolConfig:
    """Tests for PoolConfig dataclass."""

    def test_defaults(self) -> None:
        config = PoolConfig()
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_expiry == 30.0
        assert config.connect_timeout == 5.0
        assert config.read_timeout == 60.0

    def test_custom_values(self) -> None:
        config = PoolConfig(
            max_connections=200,
            max_keepalive_connections=50,
            keepalive_expiry=60.0,
            connect_timeout=10.0,
            read_timeout=120.0,
        )
        assert config.max_connections == 200
        assert config.read_timeout == 120.0


class TestConnectionPoolManager:
    """Tests for ConnectionPoolManager."""

    async def test_get_client_creates_new(self) -> None:
        """get_client creates a new client on first call."""
        manager = ConnectionPoolManager()
        client = manager.get_client("test", "http://localhost:8080")
        assert client is not None
        assert not client.is_closed
        await manager.close_all()

    async def test_get_client_returns_same_instance(self) -> None:
        """get_client returns cached client on subsequent calls."""
        manager = ConnectionPoolManager()
        client1 = manager.get_client("svc", "http://localhost:8080")
        client2 = manager.get_client("svc", "http://localhost:8080")
        assert client1 is client2
        await manager.close_all()

    async def test_different_names_different_clients(self) -> None:
        """Different names create different clients."""
        manager = ConnectionPoolManager()
        client1 = manager.get_client("svc1", "http://localhost:8080")
        client2 = manager.get_client("svc2", "http://localhost:9090")
        assert client1 is not client2
        await manager.close_all()

    async def test_close_all(self) -> None:
        """close_all closes all managed clients."""
        manager = ConnectionPoolManager()
        client = manager.get_client("test", "http://localhost:8080")
        await manager.close_all()
        assert client.is_closed

    async def test_get_stats(self) -> None:
        """get_stats returns info about active clients."""
        manager = ConnectionPoolManager()
        manager.get_client("svc1", "http://localhost:8080")
        stats = manager.get_stats()
        assert "svc1" in stats
        assert stats["svc1"]["active"] == 1
        await manager.close_all()

    async def test_custom_config(self) -> None:
        """ConnectionPoolManager respects custom PoolConfig."""
        config = PoolConfig(connect_timeout=1.0, read_timeout=2.0)
        manager = ConnectionPoolManager(config=config)
        client = manager.get_client("test", "http://localhost:8080")
        assert client is not None
        await manager.close_all()
