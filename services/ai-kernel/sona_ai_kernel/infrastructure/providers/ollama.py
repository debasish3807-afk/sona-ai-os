"""Ollama LLM provider adapter.

Connects to a local or remote Ollama instance using its native API:
- POST /api/chat for completions
- GET /api/tags for model listing
- GET / for health checks
"""

import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProviderBase,
    ProviderConfig,
    ProviderHealth,
)

logger = structlog.get_logger()


class OllamaProvider(LLMProviderBase):
    """Provider adapter for Ollama API.

    Communicates with Ollama's REST API for chat completions,
    streaming responses, model listing, and health checks.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the Ollama provider with an async HTTP client.

        Args:
            config: Provider configuration including base_url.
        """
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout_seconds),
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a non-streaming chat completion via Ollama.

        Args:
            request: The completion request payload.

        Returns:
            A CompletionResponse with generated content and token counts.

        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status.
            httpx.ConnectError: If Ollama is unreachable.
        """
        payload = self._build_payload(request, stream=False)

        log = logger.bind(provider=self.name, model=request.model)
        log.info("ollama_completion_start")

        start = time.perf_counter()
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        elapsed_ms = (time.perf_counter() - start) * 1000

        data: dict[str, Any] = response.json()

        content = data.get("message", {}).get("content", "")
        tokens_input = data.get("prompt_eval_count", 0)
        tokens_output = data.get("eval_count", 0)

        log.info(
            "ollama_completion_done",
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=round(elapsed_ms, 2),
        )

        return CompletionResponse(
            content=content,
            model=request.model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            finish_reason="stop",
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream chat completion tokens from Ollama via NDJSON.

        Args:
            request: The completion request payload.

        Yields:
            String content chunks as they arrive.
        """
        payload = self._build_payload(request, stream=True)

        log = logger.bind(provider=self.name, model=request.model)
        log.info("ollama_stream_start")

        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk_data: dict[str, Any] = json.loads(line)
                    content = chunk_data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk_data.get("done", False):
                        break
                except json.JSONDecodeError:
                    log.warning("ollama_stream_invalid_json", line=line)
                    continue

    async def check_health(self) -> ProviderHealth:
        """Check Ollama availability by hitting the root endpoint.

        Returns:
            Updated ProviderHealth reflecting current status.
        """
        start = time.perf_counter()
        try:
            response = await self._client.get("/")
            elapsed_ms = (time.perf_counter() - start) * 1000
            healthy = response.status_code == 200
            self._health = ProviderHealth(
                healthy=healthy,
                last_check=datetime.now(UTC),
                latency_ms=round(elapsed_ms, 2),
                error=None if healthy else f"Status {response.status_code}",
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._health = ProviderHealth(
                healthy=False,
                last_check=datetime.now(UTC),
                latency_ms=round(elapsed_ms, 2),
                error=str(exc),
            )
            logger.warning("ollama_health_check_failed", error=str(exc))

        return self._health

    async def list_models(self) -> list[str]:
        """List available models from Ollama via GET /api/tags.

        Returns:
            A list of model name strings.
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            models_data = data.get("models", [])
            return [m.get("name", "") for m in models_data if m.get("name")]
        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("ollama_list_models_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._client.aclose()

    def _build_payload(self, request: CompletionRequest, *, stream: bool) -> dict[str, Any]:
        """Build the Ollama API request payload.

        Args:
            request: The completion request.
            stream: Whether to enable streaming.

        Returns:
            Dictionary payload for the Ollama /api/chat endpoint.
        """
        messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in request.messages
        ]

        return {
            "model": request.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
            },
        }
