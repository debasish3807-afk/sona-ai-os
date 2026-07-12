"""OpenAI-compatible provider base.

Many providers (OpenAI, DeepSeek, Mistral, Qwen, Groq) expose an OpenAI-compatible
API. This module provides a shared implementation that all of them reuse,
eliminating code duplication.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

from config.logging import get_logger
from providers.base import BaseProvider
from providers.capabilities import (
    CapabilitySet,
)
from providers.config import ProviderConfig
from providers.http_client import ProviderClient, load_api_key
from providers.types import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    FinishReason,
    ModelInfo,
    ModelType,
    ProviderID,
    StreamChunk,
    StreamEvent,
    TokenUsage,
)

logger = get_logger(__name__)


def _convert_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Convert internal ChatMessage to OpenAI format."""
    result: list[dict[str, str]] = []
    for msg in messages:
        entry: dict[str, str] = {"role": msg.role.value, "content": msg.content}
        if msg.name:
            entry["name"] = msg.name
        result.append(entry)
    return result


def _parse_finish_reason(reason: str | None) -> FinishReason:
    """Map provider finish reason string to FinishReason enum."""
    mapping: dict[str, FinishReason] = {
        "stop": FinishReason.STOP,
        "length": FinishReason.LENGTH,
        "tool_calls": FinishReason.TOOL_CALLS,
        "content_filter": FinishReason.CONTENT_FILTER,
    }
    return mapping.get(reason or "stop", FinishReason.STOP)


class OpenAICompatProvider(BaseProvider):
    """Base for all OpenAI-compatible API providers.

    Subclasses only need to set provider_id, display_name, config, and capabilities.
    The chat/stream/embed/models/health logic is fully shared.
    """

    def __init__(
        self,
        config: ProviderConfig,
        provider_id: ProviderID,
        display_name: str,
        capabilities: CapabilitySet,
        supports_tools_flag: bool = True,
        supports_vision_flag: bool = False,
    ) -> None:
        self._config = config
        self._provider_id = provider_id
        self._display_name = display_name
        self._capabilities = capabilities
        self._supports_tools_flag = supports_tools_flag
        self._supports_vision_flag = supports_vision_flag
        self._initialized = False
        self._http: ProviderClient | None = None

    @property
    def provider_id(self) -> ProviderID:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        """Load API key and create HTTP client."""
        api_key = load_api_key(self._config.api_key_env_var)
        if not api_key:
            logger.info(
                "API key not found, provider disabled",
                provider=self._provider_id.value,
                env_var=self._config.api_key_env_var,
            )
            self._initialized = False
            return

        self._http = ProviderClient(self._config, api_key)
        await self._http.initialize()
        self._initialized = True
        logger.info("Provider initialized", provider=self._provider_id.value)

    async def shutdown(self) -> None:
        """Close HTTP client."""
        if self._http:
            await self._http.close()
            self._http = None
        self._initialized = False

    def _get_http(self) -> ProviderClient:
        """Get the HTTP client."""
        if self._http is None:
            raise RuntimeError(f"Provider {self._provider_id.value} not initialized")
        return self._http

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute chat completion via OpenAI-compatible /chat/completions."""
        http = self._get_http()
        model = request.model or self._config.default_model

        payload: dict[str, Any] = {
            "model": model,
            "messages": _convert_messages(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": False,
        }
        if request.frequency_penalty:
            payload["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty:
            payload["presence_penalty"] = request.presence_penalty
        if request.stop:
            payload["stop"] = request.stop
        if request.response_format:
            payload["response_format"] = request.response_format
        if request.seed is not None:
            payload["seed"] = request.seed

        start = time.perf_counter()
        data = await http.post("/chat/completions", payload)
        latency_ms = (time.perf_counter() - start) * 1000

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        return ChatResponse(
            content=message.get("content", ""),
            model=data.get("model", model),
            provider=self._provider_id.value,
            response_id=data.get("id", ""),
            finish_reason=_parse_finish_reason(choice.get("finish_reason")),
            token_usage=TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            tool_calls=message.get("tool_calls"),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream chat completion via OpenAI-compatible SSE."""
        http = self._get_http()
        model = request.model or self._config.default_model

        payload: dict[str, Any] = {
            "model": model,
            "messages": _convert_messages(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": True,
        }
        if request.stop:
            payload["stop"] = request.stop

        yield StreamChunk(event=StreamEvent.START, model=model)

        try:
            resp = await http.post_stream("/chat/completions", payload)
            try:
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    try:
                        chunk_data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk_data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    finish = choices[0].get("finish_reason")

                    if content:
                        yield StreamChunk(event=StreamEvent.DELTA, content=content, model=model)

                    if finish:
                        usage = chunk_data.get("usage", {})
                        yield StreamChunk(
                            event=StreamEvent.DONE,
                            model=model,
                            finish_reason=_parse_finish_reason(finish),
                            metadata={
                                "prompt_eval_count": usage.get("prompt_tokens", 0),
                                "eval_count": usage.get("completion_tokens", 0),
                            },
                        )
            finally:
                await resp.aclose()

        except Exception as exc:
            yield StreamChunk(
                event=StreamEvent.ERROR,
                content=f"{self._provider_id.value} stream error: {exc}",
                model=model,
            )

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings via OpenAI-compatible /embeddings."""
        http = self._get_http()
        model = request.model or "text-embedding-3-small"

        payload: dict[str, Any] = {
            "model": model,
            "input": request.input,
        }
        if request.dimensions:
            payload["dimensions"] = request.dimensions

        data = await http.post("/embeddings", payload)

        vecs = [item["embedding"] for item in data.get("data", [])]
        usage = data.get("usage", {})

        return EmbeddingResponse(
            embeddings=vecs,
            model=model,
            provider=self._provider_id.value,
            token_usage=TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            dimensions=len(vecs[0]) if vecs else 0,
        )

    async def list_models(self) -> list[ModelInfo]:
        """List available models via /models."""
        http = self._get_http()
        try:
            data = await http.get("/models")
        except Exception:
            logger.warning("Failed to list models", provider=self._provider_id.value)
            return []

        models: list[ModelInfo] = []
        for item in data.get("data", []):
            model_id = item.get("id", "")
            models.append(
                ModelInfo(
                    model_id=model_id,
                    name=model_id,
                    provider=self._provider_id.value,
                    model_type=ModelType.CHAT,
                    supports_streaming=True,
                    supports_tools=self._supports_tools_flag,
                    supports_vision=self._supports_vision_flag,
                )
            )
        return models

    async def get_model(self, model_id: str) -> ModelInfo | None:
        """Get info for a specific model."""
        models = await self.list_models()
        for m in models:
            if m.model_id == model_id:
                return m
        return None

    def supports_tools(self) -> bool:
        return self._supports_tools_flag

    def supports_vision(self) -> bool:
        return self._supports_vision_flag

    def supports_function_calling(self) -> bool:
        return self._supports_tools_flag

    def supports_streaming(self) -> bool:
        return True

    async def health(self) -> bool:
        """Health check by listing models."""
        if not self._http:
            return False
        return await self._http.health_check("/models")
