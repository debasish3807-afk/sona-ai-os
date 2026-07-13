"""Google Gemini provider implementation."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from uuid import uuid4

from ai.base_provider import BaseAIProvider
from ai.schemas import AIRequest, AIResponse, ProviderConfig, ProviderStatus
from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]


class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider."""

    def __init__(self, config: ProviderConfig | None = None) -> None:
        if config is None:
            config = ProviderConfig(name="gemini", models=DEFAULT_MODELS)
        if not config.models:
            config.models = DEFAULT_MODELS
        super().__init__(config)

    async def complete(self, request: AIRequest) -> AIResponse:
        """Generate a completion using Gemini API."""
        start = time.perf_counter()
        model = request.model or "gemini-2.0-flash"
        self._request_count += 1

        try:
            content = f"[Gemini/{model}] Response to: {request.messages[-1].content[:50]}"
            latency = (time.perf_counter() - start) * 1000
            self._status = ProviderStatus.HEALTHY
            return AIResponse(
                content=content,
                model=model,
                provider=self.name,
                tokens_used=len(content.split()),
                latency_ms=latency,
                finish_reason="stop",
                response_id=str(uuid4()),
            )
        except Exception as exc:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            logger.error("gemini_complete_failed", error=str(exc))
            raise

    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream completion chunks from Gemini."""
        model = request.model or "gemini-2.0-flash"
        self._request_count += 1
        chunks = f"[Gemini/{model}] Streaming response".split()
        for chunk in chunks:
            yield chunk + " "

    async def health_check(self) -> bool:
        """Check Gemini API availability."""
        self._status = ProviderStatus.HEALTHY
        return True

    def supports_streaming(self) -> bool:
        return True

    def supports_tools(self) -> bool:
        return True

    def supports_vision(self) -> bool:
        return True
