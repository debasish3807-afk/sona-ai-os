"""Unit tests for the streaming engine.

Tests verify streaming with proper cleanup, error handling,
active stream counting, and token delivery.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProviderBase,
    ProviderConfig,
    ProviderHealth,
)
from sona_ai_kernel.infrastructure.streaming import StreamingEngine


class FakeStreamProvider(LLMProviderBase):
    """Fake provider for streaming tests."""

    def __init__(self, tokens: list[str] | None = None, fail_after: int = -1) -> None:
        config = ProviderConfig(name="fake-stream", base_url="http://localhost")
        super().__init__(config)
        self._tokens = tokens if tokens is not None else ["hello", " ", "world"]
        self._fail_after = fail_after

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(content="complete", model="fake", tokens_input=1, tokens_output=1)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        for i, token in enumerate(self._tokens):
            if self._fail_after >= 0 and i >= self._fail_after:
                raise RuntimeError("Stream failed mid-way")
            yield token

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, last_check=datetime.now(UTC))

    async def list_models(self) -> list[str]:
        return ["fake-model"]


class TestStreamingEngine:
    """Tests for StreamingEngine."""

    @pytest.mark.asyncio
    async def test_streams_all_tokens(self) -> None:
        """All tokens are yielded in order."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=["a", "b", "c"])
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        tokens: list[str] = []
        async for token in engine.stream_completion(provider, request):
            tokens.append(token)

        assert tokens == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_active_stream_count(self) -> None:
        """Active stream count increments and decrements."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=["a", "b"])
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        assert engine.active_streams == 0

        # Consume the stream
        async for _ in engine.stream_completion(provider, request):
            pass

        assert engine.active_streams == 0

    @pytest.mark.asyncio
    async def test_active_stream_during_streaming(self) -> None:
        """Active stream count is 1 during streaming."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=["a", "b", "c"])
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        checked = False
        async for _ in engine.stream_completion(provider, request):
            if not checked:
                assert engine.active_streams == 1
                checked = True

        # After fully consuming, count should be 0
        assert engine.active_streams == 0
        assert checked is True

    @pytest.mark.asyncio
    async def test_error_during_stream_propagates(self) -> None:
        """Errors during streaming are propagated."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=["a", "b", "c"], fail_after=1)
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        tokens: list[str] = []
        with pytest.raises(RuntimeError, match="Stream failed mid-way"):
            async for token in engine.stream_completion(provider, request):
                tokens.append(token)

        assert tokens == ["a"]

    @pytest.mark.asyncio
    async def test_cleanup_after_error(self) -> None:
        """Active stream count is decremented even after error."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=["a"], fail_after=0)
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        with pytest.raises(RuntimeError):
            async for _ in engine.stream_completion(provider, request):
                pass

        assert engine.active_streams == 0

    @pytest.mark.asyncio
    async def test_empty_stream(self) -> None:
        """Empty token list yields no tokens."""
        engine = StreamingEngine()
        provider = FakeStreamProvider(tokens=[])
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        tokens: list[str] = []
        async for token in engine.stream_completion(provider, request):
            tokens.append(token)

        assert tokens == []

    @pytest.mark.asyncio
    async def test_large_stream(self) -> None:
        """Large number of tokens are streamed correctly."""
        engine = StreamingEngine()
        expected = [f"token-{i}" for i in range(100)]
        provider = FakeStreamProvider(tokens=expected)
        request = CompletionRequest(
            messages=[{"role": "user", "content": "test"}],
            model="fake",
        )

        tokens: list[str] = []
        async for token in engine.stream_completion(provider, request):
            tokens.append(token)

        assert tokens == expected
