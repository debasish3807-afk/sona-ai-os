"""Unit tests for the OpenAI-compatible provider adapter.

Tests verify the OpenAI-compatible adapter using httpx mock transport,
covering completions, streaming (SSE), health checks, and model listing.
"""

import json

import httpx
import pytest
from sona_ai_kernel.infrastructure.providers.base import CompletionRequest, ProviderConfig
from sona_ai_kernel.infrastructure.providers.openai_compat import OpenAICompatProvider


def _make_provider(
    handler: httpx.MockTransport, api_key: str | None = "test-key"
) -> OpenAICompatProvider:
    """Create an OpenAICompatProvider with a mock transport."""
    config = ProviderConfig(name="openai", base_url="http://localhost:8080", api_key=api_key)
    provider = OpenAICompatProvider(config)
    # Replace client with mock transport
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    provider._client = httpx.AsyncClient(
        transport=handler, base_url="http://localhost:8080", headers=headers
    )
    return provider


def _completion_response() -> dict:
    """Standard OpenAI completion response."""
    return {
        "id": "chatcmpl-123",
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "I'm a helpful assistant!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
        },
    }


class TestOpenAIComplete:
    """Tests for OpenAICompatProvider.complete()."""

    @pytest.mark.asyncio
    async def test_successful_completion(self) -> None:
        """Successful completion returns content and usage."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_completion_response())

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4o",
        )

        response = await provider.complete(request)
        assert response.content == "I'm a helpful assistant!"
        assert response.tokens_input == 20
        assert response.tokens_output == 10
        assert response.model == "gpt-4o"
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_request_payload_format(self) -> None:
        """Verify the request payload matches OpenAI format."""
        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(200, json=_completion_response())

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hi"},
            ],
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1024,
            top_p=0.95,
        )

        await provider.complete(request)
        body = captured[0]
        assert body["model"] == "gpt-4o"
        assert body["temperature"] == 0.3
        assert body["max_tokens"] == 1024
        assert body["top_p"] == 0.95
        assert body["stream"] is False
        assert len(body["messages"]) == 2

    @pytest.mark.asyncio
    async def test_auth_header_set(self) -> None:
        """Verify Authorization header is set with API key."""
        captured_headers: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_headers.append(dict(request.headers))
            return httpx.Response(200, json=_completion_response())

        provider = _make_provider(httpx.MockTransport(handler), api_key="sk-test-key")
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        await provider.complete(request)
        assert "authorization" in captured_headers[0]
        assert captured_headers[0]["authorization"] == "Bearer sk-test-key"

    @pytest.mark.asyncio
    async def test_server_error_raises(self) -> None:
        """Server errors raise HTTPStatusError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": {"message": "Server error"}})

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        with pytest.raises(httpx.HTTPStatusError):
            await provider.complete(request)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self) -> None:
        """Rate limit (429) raises HTTPStatusError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "Rate limited"}})

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        with pytest.raises(httpx.HTTPStatusError):
            await provider.complete(request)

    @pytest.mark.asyncio
    async def test_empty_choices_returns_empty_content(self) -> None:
        """Empty choices array returns empty content."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-123",
                    "model": "gpt-4o",
                    "choices": [],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 0},
                },
            )

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        response = await provider.complete(request)
        assert response.content == ""


class TestOpenAIHealthCheck:
    """Tests for OpenAICompatProvider.check_health()."""

    @pytest.mark.asyncio
    async def test_healthy_when_models_endpoint_ok(self) -> None:
        """Health check succeeds when /v1/models returns 200."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": [{"id": "gpt-4o"}]})

        provider = _make_provider(httpx.MockTransport(handler))
        health = await provider.check_health()
        assert health.healthy is True
        assert health.error is None

    @pytest.mark.asyncio
    async def test_unhealthy_on_error(self) -> None:
        """Health check fails on connection error."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        provider = _make_provider(httpx.MockTransport(handler))
        health = await provider.check_health()
        assert health.healthy is False
        assert health.error is not None


class TestOpenAIListModels:
    """Tests for OpenAICompatProvider.list_models()."""

    @pytest.mark.asyncio
    async def test_lists_models(self) -> None:
        """Successfully lists models from /v1/models."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "gpt-4o", "object": "model"},
                        {"id": "gpt-3.5-turbo", "object": "model"},
                    ]
                },
            )

        provider = _make_provider(httpx.MockTransport(handler))
        models = await provider.list_models()
        assert "gpt-4o" in models
        assert "gpt-3.5-turbo" in models

    @pytest.mark.asyncio
    async def test_empty_on_error(self) -> None:
        """Returns empty list on error."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        provider = _make_provider(httpx.MockTransport(handler))
        models = await provider.list_models()
        assert models == []


class TestOpenAIStream:
    """Tests for OpenAICompatProvider.stream()."""

    @pytest.mark.asyncio
    async def test_stream_yields_sse_chunks(self) -> None:
        """Stream yields content from SSE data lines."""
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":"!"}}]}\n\n',
            "data: [DONE]\n\n",
        ]
        content = "".join(sse_lines).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=content)

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        tokens: list[str] = []
        async for token in provider.stream(request):
            tokens.append(token)

        assert "Hello" in tokens
        assert " world" in tokens
        assert "!" in tokens

    @pytest.mark.asyncio
    async def test_stream_skips_empty_delta(self) -> None:
        """Stream skips chunks with empty content in delta."""
        sse_lines = [
            'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":"data"}}]}\n\n',
            "data: [DONE]\n\n",
        ]
        content = "".join(sse_lines).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=content)

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        tokens: list[str] = []
        async for token in provider.stream(request):
            tokens.append(token)

        assert tokens == ["data"]

    @pytest.mark.asyncio
    async def test_stream_ignores_non_data_lines(self) -> None:
        """Stream ignores lines not starting with 'data: '."""
        sse_lines = [
            ": keep-alive\n\n",
            'data: {"choices":[{"delta":{"content":"ok"}}]}\n\n',
            "event: done\n\n",
            "data: [DONE]\n\n",
        ]
        content = "".join(sse_lines).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=content)

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

        tokens: list[str] = []
        async for token in provider.stream(request):
            tokens.append(token)

        assert tokens == ["ok"]
