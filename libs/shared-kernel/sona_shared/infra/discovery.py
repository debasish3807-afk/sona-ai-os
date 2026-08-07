"""Provider discovery for auto-detecting available services.

Probes configured endpoints to determine which LLM providers and
infrastructure services are available on the network.
"""

import asyncio
from dataclasses import dataclass, field

import httpx
import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class DiscoveredProvider:
    """A discovered service provider with availability metadata."""

    name: str
    url: str
    available: bool
    models: list[str] = field(default_factory=list)
    latency_ms: float = 0.0


class ProviderDiscovery:
    """Auto-discovers available LLM providers on the network.

    Probes registered endpoints and reports which services are reachable,
    along with their available models and response latency.
    """

    def __init__(self) -> None:
        self._endpoints: dict[str, str] = {}

    def register_endpoint(self, name: str, url: str) -> None:
        """Register a provider endpoint for discovery."""
        self._endpoints[name] = url.rstrip("/")

    async def discover_all(self) -> list[DiscoveredProvider]:
        """Discover all registered providers concurrently."""
        tasks = []
        for name, url in self._endpoints.items():
            if "ollama" in name.lower():
                tasks.append(self.discover_ollama(url))
            elif "openai" in name.lower():
                tasks.append(self.discover_openai(url))
            else:
                tasks.append(self._discover_generic(name, url))
        results: list[DiscoveredProvider] = await asyncio.gather(*tasks)
        return results

    async def discover_ollama(self, url: str) -> DiscoveredProvider:
        """Discover an Ollama instance and its available models."""
        import time

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check Ollama is running
                response = await client.get(url)
                if response.status_code != 200:
                    latency = (time.perf_counter() - start) * 1000
                    return DiscoveredProvider(
                        name="ollama",
                        url=url,
                        available=False,
                        latency_ms=latency,
                    )

                # List available models
                models_response = await client.get(f"{url}/api/tags")
                models: list[str] = []
                if models_response.status_code == 200:
                    data = models_response.json()
                    models = [m["name"] for m in data.get("models", [])]

                latency = (time.perf_counter() - start) * 1000
                return DiscoveredProvider(
                    name="ollama",
                    url=url,
                    available=True,
                    models=models,
                    latency_ms=latency,
                )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            await logger.adebug("discovery.ollama_failed", url=url, error=str(exc))
            return DiscoveredProvider(
                name="ollama",
                url=url,
                available=False,
                latency_ms=latency,
            )

    async def discover_openai(self, url: str, api_key: str = "") -> DiscoveredProvider:
        """Discover an OpenAI-compatible endpoint and its available models."""
        import time

        start = time.perf_counter()
        try:
            headers: dict[str, str] = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/models", headers=headers)
                latency = (time.perf_counter() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return DiscoveredProvider(
                        name="openai",
                        url=url,
                        available=True,
                        models=models,
                        latency_ms=latency,
                    )

                return DiscoveredProvider(
                    name="openai",
                    url=url,
                    available=False,
                    latency_ms=latency,
                )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            await logger.adebug("discovery.openai_failed", url=url, error=str(exc))
            return DiscoveredProvider(
                name="openai",
                url=url,
                available=False,
                latency_ms=latency,
            )

    async def _discover_generic(self, name: str, url: str) -> DiscoveredProvider:
        """Discover a generic HTTP service by probing its root endpoint."""
        import time

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                latency = (time.perf_counter() - start) * 1000
                return DiscoveredProvider(
                    name=name,
                    url=url,
                    available=response.status_code < 500,
                    latency_ms=latency,
                )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            await logger.adebug(
                "discovery.generic_failed",
                name=name,
                url=url,
                error=str(exc),
            )
            return DiscoveredProvider(
                name=name,
                url=url,
                available=False,
                latency_ms=latency,
            )
