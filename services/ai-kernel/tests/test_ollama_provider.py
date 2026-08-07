"""Unit tests for the Ollama provider adapter.

Tests verify the Ollama adapter using httpx mock transport,
covering completions, streaming, health checks, and model listing.
"""

import json

import httpx
import pytest
from sona_ai_kernel.infrastructure.providers.base import CompletionRequest, ProviderConfig
from sona_ai_kernel.infrastructure.providers.ollama import OllamaProvider


def _make_provider(handler: httpx.MockTransport) -> OllamaProvider:
    """Create an OllamaProvider with a mock transport."""
    config = ProviderConfig(name="ollama", base_url="http://localhost:11434")
    provider = OllamaProvider(config)
    # Replace the client with one using mock transport
    provider._client = httpx.AsyncClient(transport=handler, base_url="http://localhost:11434")
    return provider


def _completion_response() -> dict:
    """Standard Ollama completion response."""
    return {
        "model": "llama3.2",
        "message": {"role": "assistant", "content": "Hello! How can I help?"},
        "done": True,
        "prompt_eval_count": 15,
        "eval_count": 8,
    }


class TestOllamaComplete:
    """Tests for OllamaProvider.complete()."""

    @pytest.mark.asyncio
    async def test_successful_completion(self) -> None:
        """Successful completion returns content and token counts."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_completion_response())

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama3.2",
        )

        response = await provider.complete(request)
        assert response.content == "Hello! How can I help?"
        assert response.tokens_input == 15
        assert response.tokens_output == 8
        assert response.model == "llama3.2"

    @pytest.mark.asyncio
    async def test_request_payload_format(self) -> None:
        """Verify the request payload is correctly structured."""
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            captured_body.append(body)
            return httpx.Response(200, json=_completion_response())

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3.2",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.9,
        )

        await provider.complete(request)
        body = captured_body[0]
        assert body["model"] == "llama3.2"
        assert body["stream"] is False
        assert body["messages"] == [{"role": "user", "content": "Hello"}]
        assert body["options"]["temperature"] == 0.5
        assert body["options"]["num_predict"] == 2048
        assert body["options"]["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_server_error_raises(self) -> None:
        """Server error raises HTTPStatusError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal error"})

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama3.2",
        )

        with pytest.raises(httpx.HTTPStatusError):
            await provider.complete(request)

    @pytest.mark.asyncio
    async def test_missing_fields_default_to_zero(self) -> None:
        """Missing token counts default to zero."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "model": "llama3.2",
                    "message": {"role": "assistant", "content": "response"},
                    "done": True,
                },
            )

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama3.2",
        )

        response = await provider.complete(request)
        assert response.tokens_input == 0
        assert response.tokens_output == 0


class TestOllamaHealthCheck:
    """Tests for OllamaProvider.check_health()."""

    @pytest.mark.asyncio
    async def test_healthy_when_200(self) -> None:
        """Health check succeeds when root returns 200."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="Ollama is running")

        provider = _make_provider(httpx.MockTransport(handler))
        health = await provider.check_health()
        assert health.healthy is True
        assert health.error is None
        assert health.latency_ms > 0

    @pytest.mark.asyncio
    async def test_unhealthy_on_error_status(self) -> None:
        """Health check fails on non-200 status."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        provider = _make_provider(httpx.MockTransport(handler))
        health = await provider.check_health()
        assert health.healthy is False
        assert "503" in (health.error or "")

    @pytest.mark.asyncio
    async def test_unhealthy_on_connection_error(self) -> None:
        """Health check fails on connection error."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        provider = _make_provider(httpx.MockTransport(handler))
        health = await provider.check_health()
        assert health.healthy is False
        assert health.error is not None


class TestOllamaListModels:
    """Tests for OllamaProvider.list_models()."""

    @pytest.mark.asyncio
    async def test_lists_available_models(self) -> None:
        """Successfully lists models from /api/tags."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "llama3.2", "size": 1000000},
                        {"name": "codellama", "size": 2000000},
                    ]
                },
            )

        provider = _make_provider(httpx.MockTransport(handler))
        models = await provider.list_models()
        assert "llama3.2" in models
        assert "codellama" in models
        assert len(models) == 2

    @pytest.mark.asyncio
    async def test_empty_on_error(self) -> None:
        """Returns empty list on connection error."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        provider = _make_provider(httpx.MockTransport(handler))
        models = await provider.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_empty_on_server_error(self) -> None:
        """Returns empty list on server error."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal"})

        provider = _make_provider(httpx.MockTransport(handler))
        models = await provider.list_models()
        assert models == []


class TestOllamaStream:
    """Tests for OllamaProvider.stream()."""

    @pytest.mark.asyncio
    async def test_stream_yields_content_chunks(self) -> None:
        """Stream yields content from NDJSON chunks."""
        chunks = [
            json.dumps({"message": {"content": "Hello"}, "done": False}) + "\n",
            json.dumps({"message": {"content": " world"}, "done": False}) + "\n",
            json.dumps({"message": {"content": "!"}, "done": True}) + "\n",
        ]
        content = "".join(chunks).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=content)

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama3.2",
        )

        tokens: list[str] = []
        async for token in provider.stream(request):
            tokens.append(token)

        assert "Hello" in tokens
        assert " world" in tokens
        assert "!" in tokens

    @pytest.mark.asyncio
    async def test_stream_handles_empty_content(self) -> None:
        """Stream skips chunks with empty content."""
        chunks = [
            json.dumps({"message": {"content": ""}, "done": False}) + "\n",
            json.dumps({"message": {"content": "data"}, "done": False}) + "\n",
            json.dumps({"message": {"content": ""}, "done": True}) + "\n",
        ]
        content = "".join(chunks).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=content)

        provider = _make_provider(httpx.MockTransport(handler))
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama3.2",
        )

        tokens: list[str] = []
        async for token in provider.stream(request):
            tokens.append(token)

        assert tokens == ["data"]
