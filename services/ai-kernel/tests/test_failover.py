"""Unit tests for the failover engine.

Tests verify failover execution, provider cycling, and circuit integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sona_ai_kernel.infrastructure.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)
from sona_ai_kernel.infrastructure.failover import FailoverEngine, FailoverError
from sona_ai_kernel.infrastructure.provider_priority import (
    ProviderPriority,
    ProviderPriorityManager,
)
from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
    ProviderConfig,
)
from sona_ai_kernel.infrastructure.registry import ProviderRegistry


def _make_request() -> CompletionRequest:
    return CompletionRequest(
        messages=[{"role": "user", "content": "hello"}],
        model="test-model",
    )


def _make_response(content: str = "response") -> CompletionResponse:
    return CompletionResponse(
        content=content,
        model="test-model",
        tokens_input=10,
        tokens_output=5,
    )


def _make_mock_provider(
    name: str, response: CompletionResponse | None = None, error: Exception | None = None
):
    """Create a mock provider for testing."""
    provider = MagicMock()
    provider.name = name
    provider.config = ProviderConfig(name=name, base_url="http://localhost")
    if error:
        provider.complete = AsyncMock(side_effect=error)
        provider.stream = MagicMock(side_effect=error)
    else:
        provider.complete = AsyncMock(return_value=response or _make_response())
        provider.stream = MagicMock(return_value=iter([]))
    return provider


class TestFailoverEngine:
    """Tests for the FailoverEngine."""

    @pytest.mark.asyncio
    async def test_success_on_first_provider(self) -> None:
        """Succeeds on the first provider without failover."""
        registry = ProviderRegistry()
        provider = _make_mock_provider("openai", _make_response("hello"))
        registry.register(provider)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="openai"))

        engine = FailoverEngine(registry, priority_mgr)
        result = await engine.execute(_make_request())

        assert result.content == "hello"
        provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_failover_to_second_provider(self) -> None:
        """Fails over to second provider when first fails."""
        registry = ProviderRegistry()
        failing = _make_mock_provider("failing", error=RuntimeError("down"))
        working = _make_mock_provider("working", _make_response("ok"))
        registry.register(failing)
        registry.register(working)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="failing", priority=1))
        priority_mgr.add(ProviderPriority(provider_name="working", priority=2))

        engine = FailoverEngine(registry, priority_mgr)
        result = await engine.execute(_make_request())

        assert result.content == "ok"

    @pytest.mark.asyncio
    async def test_raises_failover_error_when_all_fail(self) -> None:
        """Raises FailoverError when all providers fail."""
        registry = ProviderRegistry()
        provider1 = _make_mock_provider("p1", error=RuntimeError("fail"))
        provider2 = _make_mock_provider("p2", error=RuntimeError("fail"))
        registry.register(provider1)
        registry.register(provider2)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="p1"))
        priority_mgr.add(ProviderPriority(provider_name="p2"))

        engine = FailoverEngine(registry, priority_mgr)

        with pytest.raises(FailoverError) as exc_info:
            await engine.execute(_make_request())

        assert "p1" in exc_info.value.failed_providers
        assert "p2" in exc_info.value.failed_providers

    @pytest.mark.asyncio
    async def test_preferred_provider_tried_first(self) -> None:
        """Preferred provider is tried before priority order."""
        registry = ProviderRegistry()
        preferred = _make_mock_provider("preferred", _make_response("preferred"))
        primary = _make_mock_provider("primary", _make_response("primary"))
        registry.register(preferred)
        registry.register(primary)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="primary", priority=1))
        priority_mgr.add(ProviderPriority(provider_name="preferred", priority=2))

        engine = FailoverEngine(registry, priority_mgr)
        result = await engine.execute(_make_request(), preferred_provider="preferred")

        assert result.content == "preferred"

    @pytest.mark.asyncio
    async def test_skips_provider_with_open_circuit(self) -> None:
        """Skips providers whose circuit breaker is OPEN."""
        registry = ProviderRegistry()
        blocked = _make_mock_provider("blocked", _make_response("blocked"))
        working = _make_mock_provider("working", _make_response("ok"))
        registry.register(blocked)
        registry.register(working)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="blocked", priority=1))
        priority_mgr.add(ProviderPriority(provider_name="working", priority=2))

        # Create an open circuit breaker for "blocked"
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("blocked", config)
        breaker.record_failure()  # Opens the circuit

        engine = FailoverEngine(registry, priority_mgr, {"blocked": breaker})
        result = await engine.execute(_make_request())

        assert result.content == "ok"
        blocked.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_records_success_on_circuit_breaker(self) -> None:
        """Records success on the circuit breaker after successful call."""
        registry = ProviderRegistry()
        provider = _make_mock_provider("openai", _make_response("ok"))
        registry.register(provider)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="openai"))

        breaker = CircuitBreaker("openai")
        engine = FailoverEngine(registry, priority_mgr, {"openai": breaker})
        await engine.execute(_make_request())

        assert breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_records_failure_on_circuit_breaker(self) -> None:
        """Records failure on the circuit breaker after failed call."""
        registry = ProviderRegistry()
        provider = _make_mock_provider("openai", error=RuntimeError("err"))
        registry.register(provider)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="openai"))

        breaker = CircuitBreaker("openai")
        engine = FailoverEngine(registry, priority_mgr, {"openai": breaker})

        with pytest.raises(FailoverError):
            await engine.execute(_make_request())

        assert breaker._failure_count == 1

    @pytest.mark.asyncio
    async def test_stream_failover(self) -> None:
        """Stream failover falls over to next provider on error."""
        registry = ProviderRegistry()
        failing = _make_mock_provider("failing", error=RuntimeError("down"))
        working = _make_mock_provider("working")

        async def mock_stream(*args, **kwargs):
            yield "hello"

        working.stream = MagicMock(return_value=mock_stream())
        registry.register(failing)
        registry.register(working)

        priority_mgr = ProviderPriorityManager()
        priority_mgr.add(ProviderPriority(provider_name="failing", priority=1))
        priority_mgr.add(ProviderPriority(provider_name="working", priority=2))

        engine = FailoverEngine(registry, priority_mgr)
        result = await engine.execute_stream(_make_request())

        assert result is not None
