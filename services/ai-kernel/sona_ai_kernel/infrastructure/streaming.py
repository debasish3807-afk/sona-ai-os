"""Streaming response engine with backpressure and cancellation.

Manages streaming responses from LLM providers with proper error
handling, cleanup, and logging.
"""

from collections.abc import AsyncIterator

import structlog

from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    LLMProviderBase,
)

logger = structlog.get_logger()


class StreamingEngine:
    """Manages streaming responses from providers with proper cleanup.

    Wraps provider streaming calls with error handling, token counting,
    and structured logging for observability.
    """

    def __init__(self) -> None:
        """Initialize the streaming engine."""
        self._active_streams: int = 0

    @property
    def active_streams(self) -> int:
        """Return the count of currently active streams."""
        return self._active_streams

    async def stream_completion(
        self,
        provider: LLMProviderBase,
        request: CompletionRequest,
    ) -> AsyncIterator[str]:
        """Stream tokens from a provider with error handling and cleanup.

        Args:
            provider: The LLM provider to stream from.
            request: The completion request payload.

        Yields:
            String content chunks as they arrive from the provider.
        """
        log = logger.bind(provider=provider.name, model=request.model)
        log.info("stream_started")

        self._active_streams += 1
        token_count = 0

        try:
            stream = provider.stream(request)
            async for token in stream:
                token_count += 1
                yield token
        except Exception as exc:
            log.error("stream_error", error=str(exc), tokens_received=token_count)
            raise
        finally:
            self._active_streams -= 1
            log.info("stream_completed", tokens_received=token_count)
