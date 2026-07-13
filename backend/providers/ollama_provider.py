"""Ollama local model provider — full implementation.

Provides access to locally-hosted models via Ollama (LLaMA, Mistral,
CodeLlama, Phi, Gemma, etc.). Ideal for privacy-focused deployments
and offline use.

Ollama API reference:
    - POST /api/chat         — Chat completion
    - POST /api/generate     — Text completion
    - POST /api/embed        — Embeddings
    - GET  /api/tags         — List local models
    - GET  /                 — Health check
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from config.logging import get_logger
from providers.base import BaseProvider
from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import OllamaConfig, ProviderConfig
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


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text using ~4 chars per token heuristic."""
    return max(1, len(text) // 4)


def _convert_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Convert ChatMessage list to Ollama message format."""
    result: list[dict[str, str]] = []
    for msg in messages:
        entry: dict[str, str] = {"role": msg.role.value, "content": msg.content}
        if msg.name:
            entry["content"] = f"[{msg.name}]: {msg.content}"
        result.append(entry)
    return result


class OllamaProvider(BaseProvider):
    """Ollama local model provider — complete implementation.

    Supports: Any model available via Ollama (LLaMA 3, Mistral,
              CodeLlama, Phi, Gemma, Qwen, DeepSeek, etc.)
    Capabilities: chat, streaming, embeddings, code generation.
    Note: Runs locally — no API key required, no rate limits.
    """

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self._config = config or OllamaConfig()
        self._initialized = False
        self._client: httpx.AsyncClient | None = None
        self._capabilities = CapabilitySet(
            provider_id=ProviderID.OLLAMA,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.EMBEDDINGS, CapabilityLevel.INTERMEDIATE),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.INTERMEDIATE),
            ],
        )

    @property
    def provider_id(self) -> ProviderID:
        return ProviderID.OLLAMA

    @property
    def display_name(self) -> str:
        return "Ollama (Local)"

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def base_url(self) -> str:
        return self._config.base_url.rstrip("/")

    async def initialize(self) -> None:
        """Initialize the HTTP client and verify Ollama server reachability."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self._config.timeout_seconds, connect=10.0),
        )
        try:
            resp = await self._client.get("/")
            if resp.status_code == 200:
                self._initialized = True
                logger.info("Ollama provider initialized", base_url=self.base_url)
            else:
                logger.warning(
                    "Ollama server responded with non-200",
                    status=resp.status_code,
                    base_url=self.base_url,
                )
                self._initialized = True  # Still mark initialized for later retries
        except httpx.ConnectError:
            logger.warning("Ollama server not reachable", base_url=self.base_url)
            self._initialized = True  # Allow lazy connection

    async def shutdown(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._initialized = False
        logger.info("Ollama provider shut down")

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating one if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self._config.timeout_seconds, connect=10.0),
            )
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute a chat completion via Ollama /api/chat."""
        client = self._get_client()
        model = request.model or self._config.default_model
        messages = _convert_messages(request.messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
            },
        }
        if request.stop:
            payload["options"]["stop"] = request.stop

        start = time.perf_counter()
        try:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Ollama server unreachable at {self.base_url}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc.response.status_code} {exc.response.text}"
            ) from exc

        latency_ms = (time.perf_counter() - start) * 1000
        data = resp.json()

        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", _estimate_tokens(str(messages)))
        completion_tokens = data.get("eval_count", _estimate_tokens(content))

        return ChatResponse(
            content=content,
            model=model,
            provider=self.provider_id.value,
            finish_reason=FinishReason.STOP,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream chat completion via Ollama /api/chat with stream=true."""
        client = self._get_client()
        model = request.model or self._config.default_model
        messages = _convert_messages(request.messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
            },
        }
        if request.stop:
            payload["options"]["stop"] = request.stop

        yield StreamChunk(event=StreamEvent.START, model=model)

        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    import json

                    chunk_data = json.loads(line)
                    done = chunk_data.get("done", False)
                    content = chunk_data.get("message", {}).get("content", "")

                    if content:
                        yield StreamChunk(event=StreamEvent.DELTA, content=content, model=model)

                    if done:
                        yield StreamChunk(
                            event=StreamEvent.DONE,
                            model=model,
                            finish_reason=FinishReason.STOP,
                            metadata={
                                "prompt_eval_count": chunk_data.get("prompt_eval_count", 0),
                                "eval_count": chunk_data.get("eval_count", 0),
                            },
                        )
        except httpx.ConnectError:
            yield StreamChunk(
                event=StreamEvent.ERROR,
                content=f"Ollama server unreachable at {self.base_url}",
                model=model,
            )
        except httpx.HTTPStatusError as exc:
            yield StreamChunk(
                event=StreamEvent.ERROR,
                content=f"Ollama error: {exc.response.status_code}",
                model=model,
            )

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings via Ollama /api/embed."""
        client = self._get_client()
        model = request.model or "nomic-embed-text"

        all_embeddings: list[list[float]] = []
        total_tokens = 0

        for text in request.input:
            payload: dict[str, Any] = {"model": model, "input": text}
            try:
                resp = await client.post("/api/embed", json=payload)
                resp.raise_for_status()
                data = resp.json()
                embeddings_data = data.get("embeddings", [[]])
                if embeddings_data:
                    all_embeddings.append(embeddings_data[0])
                total_tokens += _estimate_tokens(text)
            except (httpx.ConnectError, httpx.HTTPStatusError) as exc:
                raise RuntimeError(f"Ollama embeddings failed: {exc}") from exc

        dimensions = len(all_embeddings[0]) if all_embeddings else 0
        return EmbeddingResponse(
            embeddings=all_embeddings,
            model=model,
            provider=self.provider_id.value,
            token_usage=TokenUsage(prompt_tokens=total_tokens, total_tokens=total_tokens),
            dimensions=dimensions,
        )

    async def list_models(self) -> list[ModelInfo]:
        """Query Ollama /api/tags for locally available models."""
        client = self._get_client()
        try:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
        except (httpx.ConnectError, httpx.HTTPStatusError):
            logger.warning("Failed to list Ollama models")
            return []

        data = resp.json()
        models: list[ModelInfo] = []
        for model_data in data.get("models", []):
            name = model_data.get("name", "")
            model_type = ModelType.CHAT
            if "embed" in name.lower():
                model_type = ModelType.EMBEDDING
            elif "code" in name.lower():
                model_type = ModelType.CODE

            models.append(
                ModelInfo(
                    model_id=name,
                    name=model_data.get("name", name),
                    provider=self.provider_id.value,
                    model_type=model_type,
                    max_context_tokens=model_data.get("details", {}).get("context_length", 8192),
                    supports_streaming=True,
                    supports_tools=False,
                    supports_vision="llava" in name.lower() or "vision" in name.lower(),
                    metadata={
                        "size": model_data.get("size", 0),
                        "modified_at": model_data.get("modified_at", ""),
                        "family": model_data.get("details", {}).get("family", ""),
                        "parameter_size": model_data.get("details", {}).get("parameter_size", ""),
                    },
                )
            )
        return models

    async def get_model(self, model_id: str) -> ModelInfo | None:
        """Get info for a specific model by ID."""
        models = await self.list_models()
        for m in models:
            if m.model_id == model_id or m.model_id.startswith(model_id):
                return m
        return None

    def supports_tools(self) -> bool:
        return False

    def supports_vision(self) -> bool:
        return False

    def supports_function_calling(self) -> bool:
        return False

    def supports_streaming(self) -> bool:
        return True

    async def health(self) -> bool:
        """Check Ollama server connectivity."""
        client = self._get_client()
        try:
            resp = await client.get("/", timeout=5.0)
            return bool(resp.status_code == 200)
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
