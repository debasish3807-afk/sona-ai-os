"""Unified AI interface with failover support."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from ai.provider_manager import ProviderManager
from ai.retry import AIRetryPolicy
from ai.schemas import AIRequest, AIResponse, ProviderStatus, TokenUsage
from ai.token_tracker import TokenTracker
from config.logging import get_logger

logger = get_logger(__name__)


class UnifiedAI:
    """Single entry point for all AI operations with failover."""

    def __init__(self, manager: ProviderManager) -> None:
        self._manager = manager
        self._tracker = TokenTracker()
        self._retry = AIRetryPolicy()
        self._total_requests = 0
        self._total_failures = 0

    async def complete(self, request: AIRequest) -> AIResponse:
        """Complete a request using default or specified provider."""
        self._total_requests += 1

        if request.provider:
            provider = self._manager.get(request.provider)
        else:
            provider = self._manager.get_default()

        if provider is None:
            self._total_failures += 1
            msg = "No provider available"
            raise RuntimeError(msg)

        try:
            result = await self._retry.execute(provider.complete, request)
            response: AIResponse = result
            self._tracker.record(
                provider=response.provider,
                model=response.model,
                prompt_tokens=response.tokens_used,
                completion_tokens=0,
            )
            return response
        except Exception:
            self._total_failures += 1
            return await self.complete_with_failover(request)

    async def stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream a response from the specified or default provider."""
        if request.provider:
            provider = self._manager.get(request.provider)
        else:
            provider = self._manager.get_default()

        if provider is None:
            msg = "No provider available"
            raise RuntimeError(msg)

        if not provider.supports_streaming():
            msg = f"Provider {provider.name} does not support streaming"
            raise RuntimeError(msg)

        async for chunk in provider.stream(request):
            yield chunk

    async def complete_with_failover(self, request: AIRequest) -> AIResponse:
        """Try all healthy providers until one succeeds."""
        providers = self._manager.list_all()

        for name in providers:
            provider = self._manager.get(name)
            if provider is None:
                continue
            if provider.get_status() == ProviderStatus.UNAVAILABLE:
                continue

            try:
                response = await provider.complete(request)
                self._tracker.record(
                    provider=response.provider,
                    model=response.model,
                    prompt_tokens=response.tokens_used,
                    completion_tokens=0,
                )
                return response
            except Exception:
                logger.warning("failover_provider_failed", provider=name)
                continue

        msg = "All providers failed"
        raise RuntimeError(msg)

    def get_token_usage(self) -> TokenUsage:
        """Get accumulated token usage."""
        return self._tracker.get_total()

    def get_stats(self) -> dict:
        """Get usage statistics."""
        usage = self._tracker.get_total()
        return {
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "token_usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": usage.cost_usd,
            },
            "providers": self._manager.get_stats(),
        }
