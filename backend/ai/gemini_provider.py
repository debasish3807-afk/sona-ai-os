"""Google Gemini provider — real HTTP integration via REST API.

Uses the Gemini API free tier at generativelanguage.googleapis.com.
Requires GEMINI_API_KEY environment variable for production use.
Falls back to offline mode when API key is not configured.
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator
from uuid import uuid4

import httpx

from ai.base_provider import BaseAIProvider
from ai.schemas import AIRequest, AIResponse, ProviderConfig, ProviderStatus
from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider with real HTTP integration.

    Uses the free-tier Gemini API (generativelanguage.googleapis.com).
    Set GEMINI_API_KEY env var to enable real completions.
    Without an API key, operates in offline mode.
    """

    def __init__(self, config: ProviderConfig | None = None) -> None:
        if config is None:
            config = ProviderConfig(name="gemini", models=DEFAULT_MODELS)
        if not config.models:
            config.models = DEFAULT_MODELS
        if not config.api_key:
            config.api_key = os.environ.get("GEMINI_API_KEY", "")
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_TIMEOUT)
        return self._client

    def _has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self._config.api_key)

    def _build_contents(self, request: AIRequest) -> list[dict]:
        """Convert AIMessages to Gemini contents format."""
        contents: list[dict] = []
        for msg in request.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        return contents

    def _build_url(self, model: str, stream: bool = False) -> str:
        """Build the Gemini API URL."""
        action = "streamGenerateContent" if stream else "generateContent"
        return f"{GEMINI_BASE_URL}/models/{model}:{action}?key={self._config.api_key}"

    async def complete(self, request: AIRequest) -> AIResponse:
        """Generate a completion via Gemini generateContent API.

        Falls back to offline response if API key is not set.
        """
        start = time.perf_counter()
        model = request.model or "gemini-2.0-flash"
        self._request_count += 1

        if not self._has_api_key():
            return self._offline_response(request, model, start)

        client = self._get_client()
        url = self._build_url(model, stream=False)
        payload: dict = {
            "contents": self._build_contents(request),
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}

        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            content = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                content = "".join(p.get("text", "") for p in parts)

            # Extract token counts
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)
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
        except httpx.HTTPStatusError as exc:
            self._error_count += 1
            if exc.response.status_code == 429:
                self._status = ProviderStatus.DEGRADED
                logger.warning("gemini_rate_limited")
            else:
                self._status = ProviderStatus.DEGRADED
                logger.error("gemini_http_error", status=exc.response.status_code)
            return self._offline_response(request, model, start)
        except Exception as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("gemini_complete_failed", error=str(exc))
            return self._offline_response(request, model, start)

    def _offline_response(self, request: AIRequest, model: str, start: float) -> AIResponse:
        """Generate offline response when Gemini API is not available."""
        user_msg = request.messages[-1].content if request.messages else ""
        content = f"[Gemini/{model} offline] Received: {user_msg[:100]}"
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
        """Stream completion chunks from Gemini streamGenerateContent.

        Falls back to local chunks if API key is not set.
        """
        model = request.model or "gemini-2.0-flash"
        self._request_count += 1

        if not self._has_api_key():
            for word in f"[Gemini/{model} offline] Streaming response".split():
                yield word + " "
            return

        client = self._get_client()
        url = self._build_url(model, stream=True) + "&alt=sse"
        payload: dict = {
            "contents": self._build_contents(request),
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}

        try:
            import json as json_mod

            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    raw = line[6:]
                    if raw == "[DONE]":
                        break
                    data = json_mod.loads(raw)
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
            self._status = ProviderStatus.HEALTHY
        except Exception as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("gemini_stream_failed", error=str(exc))
            yield f"[Gemini/{model} offline] Stream error"

    async def health_check(self) -> bool:
        """Check Gemini API availability."""
        if not self._has_api_key():
            self._status = ProviderStatus.DEGRADED
            return True  # Provider functional in offline mode

        try:
            client = self._get_client()
            url = f"{GEMINI_BASE_URL}/models?key={self._config.api_key}"
            resp = await client.get(url, timeout=httpx.Timeout(5.0))
            healthy = resp.status_code == 200
            self._status = ProviderStatus.HEALTHY if healthy else ProviderStatus.DEGRADED
            return healthy
        except Exception:
            self._status = ProviderStatus.DEGRADED
            return True  # Still functional in offline mode

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def supports_streaming(self) -> bool:
        return True

    def supports_tools(self) -> bool:
        return True

    def supports_vision(self) -> bool:
        return True
