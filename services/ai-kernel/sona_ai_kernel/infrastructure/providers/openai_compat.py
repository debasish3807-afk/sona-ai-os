"""OpenAI-compatible LLM provider adapter.

Connects to any OpenAI API-compatible endpoint (OpenAI, Azure OpenAI,
Anthropic via proxy, vLLM, LiteLLM, etc.) using the standard v1 API:
- POST /v1/chat/completions for completions
- GET /v1/models for model listing
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


class OpenAICompatProvider(LLMProviderBase):
    """Provider adapter for OpenAI-compatible APIs.

    Supports any endpoint conforming to the OpenAI v1 chat completions
    specification, including streaming via Server-Sent Events (SSE).
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the OpenAI-compatible provider.

        Args:
            config: Provider configuration including base_url and api_key.
        """
        super().__init__(config)
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout_seconds),
            headers=headers,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a non-streaming chat completion.

        Args:
            request: The completion request payload.

        Returns:
            A CompletionResponse with generated content and usage metrics.

        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status.
            httpx.ConnectError: If the endpoint is unreachable.
        """
        payload = self._build_payload(request, stream=False)

        log = logger.bind(provider=self.name, model=request.model)
        log.info("openai_compat_completion_start")

        start = time.perf_counter()
        response = await self._client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        elapsed_ms = (time.perf_counter() - start) * 1000

        data: dict[str, Any] = response.json()

        choices = data.get("choices", [])
        content = ""
        finish_reason = "stop"
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            finish_reason = choices[0].get("finish_reason", "stop")

        usage = data.get("usage", {})
        tokens_input = usage.get("prompt_tokens", 0)
        tokens_output = usage.get("completion_tokens", 0)

        log.info(
            "openai_compat_completion_done",
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=round(elapsed_ms, 2),
        )

        return CompletionResponse(
            content=content,
            model=data.get("model", request.model),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            finish_reason=finish_reason,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream chat completion tokens via Server-Sent Events.

        Args:
            request: The completion request payload.

        Yields:
            String content chunks as they arrive from the SSE stream.
        """
        payload = self._build_payload(request, stream=True)

        log = logger.bind(provider=self.name, model=request.model)
        log.info("openai_compat_stream_start")

        async with self._client.stream("POST", "/v1/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]  # strip "data: " prefix
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk: dict[str, Any] = json.loads(data_str)
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    log.warning("openai_compat_stream_invalid_json", line=line)
                    continue

    async def check_health(self) -> ProviderHealth:
        """Check provider availability by listing models.

        Returns:
            Updated ProviderHealth reflecting current status.
        """
        start = time.perf_counter()
        try:
            response = await self._client.get("/v1/models")
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
            logger.warning("openai_compat_health_check_failed", error=str(exc))

        return self._health

    async def list_models(self) -> list[str]:
        """List available models via GET /v1/models.

        Returns:
            A list of model identifier strings.
        """
        try:
            response = await self._client.get("/v1/models")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            models_data = data.get("data", [])
            return [m.get("id", "") for m in models_data if m.get("id")]
        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("openai_compat_list_models_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._client.aclose()

    def _build_payload(self, request: CompletionRequest, *, stream: bool) -> dict[str, Any]:
        """Build the OpenAI-compatible API request payload.

        Args:
            request: The completion request.
            stream: Whether to enable SSE streaming.

        Returns:
            Dictionary payload for the /v1/chat/completions endpoint.
        """
        return {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": stream,
        }
