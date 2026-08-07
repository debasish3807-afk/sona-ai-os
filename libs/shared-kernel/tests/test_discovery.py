"""Tests for provider discovery."""

from sona_shared.infra.discovery import DiscoveredProvider, ProviderDiscovery


class TestDiscoveredProvider:
    """Tests for DiscoveredProvider dataclass."""

    def test_create(self) -> None:
        provider = DiscoveredProvider(
            name="ollama",
            url="http://localhost:11434",
            available=True,
            models=["llama3", "mistral"],
            latency_ms=5.0,
        )
        assert provider.name == "ollama"
        assert provider.available is True
        assert len(provider.models) == 2
        assert provider.latency_ms == 5.0

    def test_defaults(self) -> None:
        provider = DiscoveredProvider(name="test", url="http://localhost", available=False)
        assert provider.models == []
        assert provider.latency_ms == 0.0


class TestProviderDiscovery:
    """Tests for ProviderDiscovery."""

    def test_register_endpoint(self) -> None:
        discovery = ProviderDiscovery()
        discovery.register_endpoint("ollama", "http://localhost:11434")
        assert "ollama" in discovery._endpoints  # noqa: SLF001

    async def test_discover_ollama_unavailable(self) -> None:
        """Ollama discovery returns unavailable when host is unreachable."""
        discovery = ProviderDiscovery()
        result = await discovery.discover_ollama("http://nonexistent:99999")
        assert result.available is False
        assert result.name == "ollama"
        assert result.latency_ms > 0

    async def test_discover_openai_unavailable(self) -> None:
        """OpenAI discovery returns unavailable when host is unreachable."""
        discovery = ProviderDiscovery()
        result = await discovery.discover_openai("http://nonexistent:99999")
        assert result.available is False
        assert result.name == "openai"

    async def test_discover_all_empty(self) -> None:
        """discover_all with no registered endpoints returns empty list."""
        discovery = ProviderDiscovery()
        results = await discovery.discover_all()
        assert results == []

    async def test_discover_all_unreachable(self) -> None:
        """discover_all handles unreachable endpoints gracefully."""
        discovery = ProviderDiscovery()
        discovery.register_endpoint("ollama", "http://nonexistent:11434")
        discovery.register_endpoint("openai", "http://nonexistent:8080")
        results = await discovery.discover_all()
        assert len(results) == 2
        assert all(not r.available for r in results)
