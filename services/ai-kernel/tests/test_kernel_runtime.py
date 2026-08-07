"""Unit tests for the AI Kernel runtime.

Tests verify the full runtime pipeline with mock providers,
including process, stream, model selection, and error handling.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest

from sona_ai_kernel.application.ports import AIKernelPort
from sona_ai_kernel.domain.events import (
    InferenceCompletedEvent,
    InferenceFailedEvent,
    InferenceStartedEvent,
)
from sona_ai_kernel.domain.models import KernelRequest, ModelConfig
from sona_ai_kernel.infrastructure.kernel_runtime import AIKernelRuntime
from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProviderBase,
    ProviderConfig,
    ProviderHealth,
)
from sona_ai_kernel.infrastructure.registry import ModelRegistry, ProviderRegistry
from sona_ai_kernel.infrastructure.retry import RetryConfig
from sona_ai_kernel.infrastructure.token_usage import TokenUsageManager


class MockProvider(LLMProviderBase):
    """Mock provider for runtime testing."""

    def __init__(
        self,
        name: str = "mock",
        response_content: str = "Hello from mock!",
        fail: bool = False,
    ) -> None:
        config = ProviderConfig(name=name, base_url="http://mock")
        super().__init__(config)
        self._response_content = response_content
        self._fail = fail

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if self._fail:
            raise RuntimeError("Provider failed")
        return CompletionResponse(
            content=self._response_content,
            model=request.model,
            tokens_input=10,
            tokens_output=5,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        if self._fail:
            raise RuntimeError("Provider stream failed")
        for word in self._response_content.split():
            yield word + " "

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(healthy=not self._fail, last_check=datetime.now(UTC))

    async def list_models(self) -> list[str]:
        return ["mock-model"]


def _make_runtime(
    provider_name: str = "mock",
    response_content: str = "Hello!",
    fail: bool = False,
    default_model: str = "mock-model",
) -> AIKernelRuntime:
    """Helper to create a runtime with a mock provider."""
    provider_registry = ProviderRegistry()
    provider = MockProvider(name=provider_name, response_content=response_content, fail=fail)
    provider_registry.register(provider)

    model_registry = ModelRegistry(provider_registry)
    model_registry.register_model(default_model, provider_name)

    token_manager = TokenUsageManager()

    return AIKernelRuntime(
        provider_registry=provider_registry,
        model_registry=model_registry,
        token_manager=token_manager,
        default_model=default_model,
        default_provider=provider_name,
        retry_config=RetryConfig(max_retries=0, base_delay=0.01),
    )


class TestAIKernelRuntimeInterface:
    """Verify the runtime implements AIKernelPort."""

    def test_implements_port(self) -> None:
        """AIKernelRuntime is an instance of AIKernelPort."""
        runtime = _make_runtime()
        assert isinstance(runtime, AIKernelPort)


class TestProcess:
    """Tests for AIKernelRuntime.process()."""

    @pytest.mark.asyncio
    async def test_process_returns_response(self) -> None:
        """Process returns a valid KernelResponse."""
        runtime = _make_runtime(response_content="Test response")
        request = KernelRequest(session_id="s1", user_id="u1", content="Hello")

        response = await runtime.process(request)
        assert response.content == "Test response"
        assert response.model_used == "mock-model"
        assert response.tokens_input == 10
        assert response.tokens_output == 5
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_process_records_usage(self) -> None:
        """Process records token usage."""
        runtime = _make_runtime()
        request = KernelRequest(session_id="s1", user_id="u1", content="Hello")

        await runtime.process(request)
        usage = runtime._token_manager.get_session_usage("s1")
        assert usage["tokens_input"] == 10
        assert usage["tokens_output"] == 5

    @pytest.mark.asyncio
    async def test_process_emits_started_and_completed_events(self) -> None:
        """Process emits InferenceStarted and InferenceCompleted events."""
        runtime = _make_runtime()
        request = KernelRequest(session_id="s1", user_id="u1", content="Hello")

        await runtime.process(request)
        events = runtime.events
        assert len(events) == 2
        assert isinstance(events[0], InferenceStartedEvent)
        assert isinstance(events[1], InferenceCompletedEvent)

    @pytest.mark.asyncio
    async def test_process_failure_emits_failed_event(self) -> None:
        """Process failure emits InferenceFailed event."""
        runtime = _make_runtime(fail=True)
        request = KernelRequest(session_id="s1", user_id="u1", content="Hello")

        with pytest.raises(RuntimeError, match="Provider failed"):
            await runtime.process(request)

        events = runtime.events
        assert len(events) == 2
        assert isinstance(events[0], InferenceStartedEvent)
        assert isinstance(events[1], InferenceFailedEvent)
        assert "Provider failed" in events[1].error

    @pytest.mark.asyncio
    async def test_process_with_model_override(self) -> None:
        """Process uses model_override when provided."""
        runtime = _make_runtime()
        override = ModelConfig(provider="mock", model_id="custom-model")
        request = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="Hello",
            model_override=override,
        )

        response = await runtime.process(request)
        assert response.model_used == "custom-model"

    @pytest.mark.asyncio
    async def test_process_with_context(self) -> None:
        """Process handles context with system message."""
        runtime = _make_runtime()
        request = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="Hello",
            context={"system": "You are helpful"},
        )

        response = await runtime.process(request)
        assert response.content == "Hello!"


class TestStream:
    """Tests for AIKernelRuntime.stream()."""

    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self) -> None:
        """Stream yields individual tokens."""
        runtime = _make_runtime(response_content="Hello world test")
        request = KernelRequest(session_id="s1", user_id="u1", content="Hi")

        tokens: list[str] = []
        async for token in runtime.stream(request):
            tokens.append(token)

        assert len(tokens) == 3
        assert "Hello " in tokens

    @pytest.mark.asyncio
    async def test_stream_error_propagates(self) -> None:
        """Stream errors are propagated to the caller."""
        runtime = _make_runtime(fail=True)
        request = KernelRequest(session_id="s1", user_id="u1", content="Hi")

        with pytest.raises(RuntimeError, match="Provider stream failed"):
            async for _ in runtime.stream(request):
                pass

    @pytest.mark.asyncio
    async def test_stream_provider_not_found(self) -> None:
        """Stream raises error when provider not found."""
        runtime = _make_runtime()
        override = ModelConfig(provider="nonexistent", model_id="m")
        request = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="Hi",
            model_override=override,
        )

        with pytest.raises(RuntimeError, match="not found"):
            async for _ in runtime.stream(request):
                pass


class TestSelectModel:
    """Tests for AIKernelRuntime.select_model()."""

    @pytest.mark.asyncio
    async def test_uses_model_override(self) -> None:
        """select_model returns the override when provided."""
        runtime = _make_runtime()
        override = ModelConfig(provider="custom", model_id="custom-m")
        request = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="test",
            model_override=override,
        )

        result = await runtime.select_model(request)
        assert result == override

    @pytest.mark.asyncio
    async def test_resolves_from_registry(self) -> None:
        """select_model resolves from model registry."""
        runtime = _make_runtime(default_model="mock-model")
        request = KernelRequest(session_id="s1", user_id="u1", content="test")

        result = await runtime.select_model(request)
        assert result.model_id == "mock-model"
        assert result.provider == "mock"

    @pytest.mark.asyncio
    async def test_falls_back_to_default_provider(self) -> None:
        """select_model uses default provider when model not in registry."""
        provider_registry = ProviderRegistry()
        provider_registry.register(MockProvider(name="fallback"))
        model_registry = ModelRegistry(provider_registry)
        # Don't register any model mapping

        runtime = AIKernelRuntime(
            provider_registry=provider_registry,
            model_registry=model_registry,
            token_manager=TokenUsageManager(),
            default_model="unregistered-model",
            default_provider="fallback",
        )
        request = KernelRequest(session_id="s1", user_id="u1", content="test")

        result = await runtime.select_model(request)
        assert result.provider == "fallback"
        assert result.model_id == "unregistered-model"


class TestEventHandling:
    """Tests for event collection and clearing."""

    @pytest.mark.asyncio
    async def test_clear_events(self) -> None:
        """clear_events empties the event list."""
        runtime = _make_runtime()
        request = KernelRequest(session_id="s1", user_id="u1", content="Hello")
        await runtime.process(request)
        assert len(runtime.events) > 0

        runtime.clear_events()
        assert len(runtime.events) == 0
