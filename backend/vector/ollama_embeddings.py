"""Ollama-based embedding engine — real local embeddings.

Uses Ollama's /api/embed endpoint for production-quality embeddings.
Default model: nomic-embed-text (768 dims) or mxbai-embed-large (1024 dims).
Falls back to hash-based embeddings if Ollama is unavailable.

Free, local, and privacy-preserving.
"""

from __future__ import annotations

import os

import httpx

from config.logging import get_logger
from vector.embeddings import EmbeddingEngine

logger = get_logger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
_TIMEOUT = httpx.Timeout(60.0, connect=5.0)


class OllamaEmbeddingEngine(EmbeddingEngine):
    """Embedding engine using Ollama's local embedding models.

    Uses real ML embeddings via Ollama /api/embed for semantic similarity.
    Falls back to hash-based embeddings if Ollama is not available.

    Recommended models (pull via `ollama pull <model>`):
        - nomic-embed-text: 768 dims, fast, good quality
        - mxbai-embed-large: 1024 dims, higher quality
        - all-minilm: 384 dims, lightweight
    """

    def __init__(
        self,
        model: str | None = None,
        ollama_url: str | None = None,
        dimensions: int = 768,
    ) -> None:
        super().__init__(dimensions=dimensions)
        self._model = model or os.environ.get("EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self._ollama_url = ollama_url or os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL)
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._ollama_url,
                timeout=_TIMEOUT,
            )
        return self._client

    async def _check_availability(self) -> bool:
        """Check if Ollama embedding is available."""
        if self._available is not None:
            return self._available
        try:
            client = self._get_client()
            resp = await client.get("/", timeout=httpx.Timeout(2.0))
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def embed_text_async(self, text: str) -> list[float]:
        """Generate embedding using Ollama /api/embed.

        Returns real ML embedding if Ollama is available,
        otherwise falls back to hash-based embedding.
        """
        if not await self._check_availability():
            return self.embed_text(text)  # Hash-based fallback

        client = self._get_client()
        try:
            resp = await client.post(
                "/api/embed",
                json={"model": self._model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [])
            if embeddings:
                vec: list[float] = embeddings[0]
                # Update dimensions to match model output
                if len(vec) != self._dimensions:
                    self._dimensions = len(vec)
                return list(vec)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning(
                    "embed_model_not_found",
                    model=self._model,
                    hint=f"Run: ollama pull {self._model}",
                )
                self._available = False
            else:
                logger.error("ollama_embed_error", status=exc.response.status_code)
        except Exception as exc:
            logger.error("ollama_embed_failed", error=str(exc))
            self._available = False

        return self.embed_text(text)  # Fallback

    async def embed_batch_async(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Uses Ollama batch API if available, otherwise sequential fallback.
        """
        if not texts:
            return []

        if not await self._check_availability():
            return self.embed_batch(texts)  # Hash-based fallback

        client = self._get_client()
        try:
            resp = await client.post(
                "/api/embed",
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [])
            if embeddings and len(embeddings) == len(texts):
                result: list[list[float]] = embeddings
                if result[0] and len(result[0]) != self._dimensions:
                    self._dimensions = len(result[0])
                return result
        except Exception as exc:
            logger.error("ollama_batch_embed_failed", error=str(exc))

        return self.embed_batch(texts)  # Fallback

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def model_name(self) -> str:
        """Current embedding model name."""
        return self._model

    @property
    def is_available(self) -> bool:
        """Whether real embeddings are available."""
        return self._available is True
