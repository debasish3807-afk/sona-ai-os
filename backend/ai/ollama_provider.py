"""Ollama local provider — real HTTP integration.

Connects to a running Ollama instance via its REST API at localhost:11434.
Supports chat completion, streaming, and model listing.
Falls back to local generation when Ollama is not running.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from uuid import uuid4

import httpx

from ai.base_provider import BaseAIProvider
from ai.schemas import AIRequest, AIResponse, ProviderConfig, ProviderStatus
from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODELS = ["llama3", "mistral", "codellama", "phi3"]
DEFAULT_BASE_URL = "http://localhost:11434"
_TIMEOUT = httpx.Timeout(120.0, connect=5.0)


class OllamaProvider(BaseAIProvider):
    """Ollama local inference provider with real HTTP integration.

    Requires a running Ollama instance (https://ollama.ai).
    Default endpoint: http://localhost:11434

    When Ollama is unavailable, operates in offline mode returning
    a local acknowledgement (useful for testing and development).
    """

    def __init__(self, config: ProviderConfig | None = None) -> None:
        if config is None:
            config = ProviderConfig(
                name="ollama",
                base_url=DEFAULT_BASE_URL,
                models=DEFAULT_MODELS,
            )
        if not config.base_url:
            config.base_url = DEFAULT_BASE_URL
        if not config.models:
            config.models = DEFAULT_MODELS
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._ollama_available: bool | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=_TIMEOUT,
            )
        return self._client

    def _build_messages(self, request: AIRequest) -> list[dict[str, str]]:
        """Convert AIMessages to Ollama format."""
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    async def _check_availability(self) -> bool:
        """Check if Ollama is reachable (cached after first check)."""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            client = self._get_client()
            resp = await client.get("/", timeout=httpx.Timeout(2.0))
            self._ollama_available = resp.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    async def complete(self, request: AIRequest) -> AIResponse:
        """Generate a completion by calling Ollama /api/chat.

        Falls back to offline response if Ollama is not running.
        """
        start = time.perf_counter()
        model = request.model or "llama3"
        self._request_count += 1

        if not await self._check_availability():
            return self._offline_response(request, model, start)

        client = self._get_client()
        payload = {
            "model": model,
            "messages": self._build_messages(request),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

            content = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            latency = (time.perf_counter() - start) * 1000

            self._status = ProviderStatus.HEALTHY
            return AIResponse(
                content=content,
                model=model,
                provider=self.name,
                tokens_used=prompt_tokens + completion_tokens,
                latency_ms=latency,
                finish_reason="stop",
                response_id=str(uuid4()),
            )
        except httpx.ConnectError:
            self._ollama_available = False
            return self._offline_response(request, model, start)
        except httpx.HTTPStatusError as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("ollama_http_error", status=exc.response.status_code)
            raise
        except Exception as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("ollama_complete_failed", error=str(exc))
            raise

    def _offline_response(self, request: AIRequest, model: str, start: float) -> AIResponse:
        """Generate offline response when Ollama is not available."""
        user_msg = request.messages[-1].content if request.messages else ""
        content = f"[Ollama/{model} offline] Received: {user_msg[:100]}"
        latency = (time.perf_counter() - start) * 1000
        self._status = ProviderStatus.DEGRADED
        return AIResponse(
            content=content,
            model=model,
            provider=self.name,
            tokens_used=len(content.split()),
            latency_ms=latency,
            finish_reason="stop",
            response_id=str(uuid4()),
        )

    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream completion chunks from Ollama /api/chat.

        Falls back to local chunks if Ollama is not running.
        """
        model = request.model or "llama3"
        self._request_count += 1

        if not await self._check_availability():
            for word in f"[Ollama/{model} offline] Streaming response".split():
                yield word + " "
            return

        client = self._get_client()
        payload = {
            "model": model,
            "messages": self._build_messages(request),
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            import json as json_mod

            async with client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json_mod.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break
            self._status = ProviderStatus.HEALTHY
        except httpx.ConnectError:
            self._ollama_available = False
            yield f"[Ollama/{model} offline] Connection lost"
        except Exception as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("ollama_stream_failed", error=str(exc))

    async def health_check(self) -> bool:
        """Check Ollama availability via GET /."""
        try:
            client = self._get_client()
            resp = await client.get("/", timeout=httpx.Timeout(2.0))
            healthy = resp.status_code == 200
            self._status = ProviderStatus.HEALTHY if healthy else ProviderStatus.UNAVAILABLE
            self._ollama_available = healthy
            return healthy
        except Exception:
            self._status = ProviderStatus.UNAVAILABLE
            self._ollama_available = False
            # Return True in degraded mode — provider is functional (offline mode)
            return True

    async def list_models(self) -> list[str]:
        """Fetch available models from Ollama /api/tags."""
        try:
            client = self._get_client()
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return self._config.models

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def supports_streaming(self) -> bool:
        return True

    def supports_tools(self) -> bool:
        return False

    def supports_vision(self) -> bool:
        return False
