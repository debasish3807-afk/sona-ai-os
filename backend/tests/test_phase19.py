"""Phase 19 tests — Production Reality Sprint.

Tests for real integrations: Ollama, Gemini, PostgreSQL, Redis, Qdrant, RAG.
All tests operate in offline/fallback mode (no external services required).
"""

from __future__ import annotations

import pytest

from ai.gemini_provider import GeminiProvider
from ai.ollama_provider import OllamaProvider
from ai.schemas import AIMessage, AIRequest, AIResponse, ProviderConfig
from rag.vector_retriever import VectorRetriever
from storage.postgres_backend import PostgresBackend
from storage.redis_cache import RedisCache
from storage.repository import DocumentRecord, MemoryRecord
from vector.ollama_embeddings import OllamaEmbeddingEngine
from vector.qdrant_store import QdrantStore

# ======================================================================
# OLLAMA PROVIDER (Real HTTP with offline fallback)
# ======================================================================


class TestOllamaProviderReal:
    """Tests for real Ollama provider with graceful offline fallback."""

    def test_create_default(self):
        provider = OllamaProvider()
        assert provider.name == "ollama"
        assert "llama3" in provider.available_models

    def test_create_with_custom_url(self):
        cfg = ProviderConfig(name="ollama", base_url="http://custom:11434", models=["mistral"])
        provider = OllamaProvider(config=cfg)
        assert "mistral" in provider.available_models

    @pytest.mark.asyncio
    async def test_complete_offline_fallback(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello test")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "ollama"
        assert resp.model == "llama3"
        assert resp.content != ""
        assert resp.response_id != ""

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        provider = OllamaProvider()
        req = AIRequest(
            messages=[AIMessage(role="user", content="test")],
            system_prompt="You are helpful.",
        )
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)

    @pytest.mark.asyncio
    async def test_complete_custom_model(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")], model="mistral")
        resp = await provider.complete(req)
        assert resp.model == "mistral"

    @pytest.mark.asyncio
    async def test_stream_offline_fallback(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="stream test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0
        combined = "".join(chunks)
        assert "Ollama" in combined

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self):
        provider = OllamaProvider()
        # Health check returns True even in offline mode (degraded but functional)
        result = await provider.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_list_models_fallback(self):
        provider = OllamaProvider()
        models = await provider.list_models()
        assert isinstance(models, list)
        assert len(models) >= 1

    @pytest.mark.asyncio
    async def test_request_count_increments(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="count")])
        await provider.complete(req)
        await provider.complete(req)
        assert provider._request_count == 2

    @pytest.mark.asyncio
    async def test_close(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="x")])
        await provider.complete(req)
        await provider.close()
        # Should be able to create new client after close
        resp = await provider.complete(req)
        assert resp.content != ""

    def test_supports_streaming(self):
        assert OllamaProvider().supports_streaming() is True

    def test_does_not_support_tools(self):
        assert OllamaProvider().supports_tools() is False

    def test_does_not_support_vision(self):
        assert OllamaProvider().supports_vision() is False


# ======================================================================
# GEMINI PROVIDER (Real HTTP with offline fallback)
# ======================================================================


class TestGeminiProviderReal:
    """Tests for real Gemini provider with offline fallback."""

    def test_create_default(self):
        provider = GeminiProvider()
        assert provider.name == "gemini"
        assert "gemini-2.0-flash" in provider.available_models

    def test_create_with_api_key(self):
        cfg = ProviderConfig(name="gemini", api_key="test-key", models=["gemini-1.5-pro"])
        provider = GeminiProvider(config=cfg)
        assert "gemini-1.5-pro" in provider.available_models

    @pytest.mark.asyncio
    async def test_complete_offline(self):
        provider = GeminiProvider()  # No API key = offline mode
        req = AIRequest(messages=[AIMessage(role="user", content="Hello")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "gemini"
        assert resp.model == "gemini-2.0-flash"
        assert "Gemini" in resp.content or "offline" in resp.content

    @pytest.mark.asyncio
    async def test_complete_custom_model(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")], model="gemini-1.5-pro")
        resp = await provider.complete(req)
        assert resp.model == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_stream_offline(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="stream")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0
        combined = "".join(chunks)
        assert "Gemini" in combined

    @pytest.mark.asyncio
    async def test_health_check_offline(self):
        provider = GeminiProvider()
        result = await provider.health_check()
        assert result is True  # Functional in offline mode

    @pytest.mark.asyncio
    async def test_close(self):
        provider = GeminiProvider()
        await provider.close()

    def test_supports_streaming(self):
        assert GeminiProvider().supports_streaming() is True

    def test_supports_tools(self):
        assert GeminiProvider().supports_tools() is True

    def test_supports_vision(self):
        assert GeminiProvider().supports_vision() is True

    @pytest.mark.asyncio
    async def test_request_count(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="x")])
        await provider.complete(req)
        assert provider._request_count == 1


# ======================================================================
# POSTGRESQL BACKEND (offline — tests graceful degradation)
# ======================================================================


class TestPostgresBackend:
    """Tests for PostgreSQL storage backend (offline mode)."""

    @pytest.mark.asyncio
    async def test_initialize_without_postgres(self):
        backend = PostgresBackend(database_url="postgresql://fake:fake@localhost:5432/fake")
        await backend.initialize()
        # Should not crash, just mark as unavailable
        assert backend.is_available is False

    @pytest.mark.asyncio
    async def test_save_document_offline(self):
        backend = PostgresBackend()
        doc = DocumentRecord(doc_id="test-1", title="Test", content="Content")
        result = await backend.save_document(doc)
        assert result == "test-1"  # Returns doc_id even when offline

    @pytest.mark.asyncio
    async def test_get_document_offline(self):
        backend = PostgresBackend()
        result = await backend.get_document("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_documents_offline(self):
        backend = PostgresBackend()
        result = await backend.list_documents()
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_document_offline(self):
        backend = PostgresBackend()
        result = await backend.delete_document("test-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_search_documents_offline(self):
        backend = PostgresBackend()
        result = await backend.search_documents("query")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_memory_offline(self):
        backend = PostgresBackend()
        mem = MemoryRecord(memory_id="m-1", content="Remember this")
        result = await backend.save_memory(mem)
        assert result == "m-1"

    @pytest.mark.asyncio
    async def test_get_memories_offline(self):
        backend = PostgresBackend()
        result = await backend.get_memories(session_id="s1")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_memories_offline(self):
        backend = PostgresBackend()
        result = await backend.search_memories("query")
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_memory_offline(self):
        backend = PostgresBackend()
        result = await backend.delete_memory("m-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_shutdown(self):
        backend = PostgresBackend()
        await backend.shutdown()  # Should not crash


# ======================================================================
# REDIS CACHE (in-memory fallback)
# ======================================================================


class TestRedisCache:
    """Tests for Redis cache with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_initialize_without_redis(self):
        cache = RedisCache(redis_url="redis://fake:6379/0")
        await cache.initialize()
        # Falls back to local cache
        assert cache.is_available is False

    @pytest.mark.asyncio
    async def test_set_and_get_local(self):
        cache = RedisCache()
        # Without initializing Redis, uses local cache
        await cache.set("key1", {"data": "value"})
        result = await cache.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_missing_key(self):
        cache = RedisCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self):
        cache = RedisCache()
        await cache.set("to_delete", "val")
        result = await cache.delete("to_delete")
        assert result is True
        assert await cache.get("to_delete") is None

    @pytest.mark.asyncio
    async def test_delete_missing(self):
        cache = RedisCache()
        result = await cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self):
        cache = RedisCache()
        await cache.set("exists_key", 42)
        assert await cache.exists("exists_key") is True
        assert await cache.exists("no_key") is False

    @pytest.mark.asyncio
    async def test_clear_prefix(self):
        cache = RedisCache()
        await cache.set("search:q1", "r1")
        await cache.set("search:q2", "r2")
        await cache.set("other:k", "v")
        count = await cache.clear_prefix("search:")
        assert count == 2
        assert await cache.get("search:q1") is None
        assert await cache.get("other:k") == "v"

    @pytest.mark.asyncio
    async def test_get_or_set(self):
        cache = RedisCache()

        async def factory():
            return {"computed": True}

        result = await cache.get_or_set("lazy_key", factory)
        assert result == {"computed": True}
        # Second call should hit cache
        result2 = await cache.get_or_set("lazy_key", factory)
        assert result2 == {"computed": True}

    @pytest.mark.asyncio
    async def test_ttl_expiry(self):
        import time

        cache = RedisCache()
        await cache.set("short_ttl", "val", ttl=0)  # 0 second TTL
        time.sleep(0.01)
        # Expired entry returns None (TTL already passed)
        result = await cache.get("short_ttl")
        assert result is None

    @pytest.mark.asyncio
    async def test_stats(self):
        cache = RedisCache()
        await cache.set("s1", "v1")
        await cache.get("s1")
        await cache.get("missing")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["backend"] == "memory"

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        cache = RedisCache()
        await cache.set("x", 1)
        cache.reset_stats()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["sets"] == 0

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        cache = RedisCache()
        # Fill past max (1000 default)
        for i in range(1010):
            await cache.set(f"item_{i}", i)
        stats = cache.get_stats()
        assert stats["local_cache_size"] <= 1000

    @pytest.mark.asyncio
    async def test_json_serializable_values(self):
        cache = RedisCache()
        await cache.set("list", [1, 2, 3])
        await cache.set("nested", {"a": {"b": [1, 2]}})
        assert await cache.get("list") == [1, 2, 3]
        assert await cache.get("nested") == {"a": {"b": [1, 2]}}

    @pytest.mark.asyncio
    async def test_shutdown(self):
        cache = RedisCache()
        await cache.shutdown()  # Should not crash


# ======================================================================
# QDRANT VECTOR STORE (offline fallback)
# ======================================================================


class TestQdrantStore:
    """Tests for Qdrant vector store (offline mode)."""

    @pytest.mark.asyncio
    async def test_initialize_offline(self):
        store = QdrantStore(qdrant_url="http://fake:6333")
        await store.initialize()
        assert store.is_available is False

    @pytest.mark.asyncio
    async def test_upsert_offline(self):
        store = QdrantStore()
        result = await store.upsert("doc-1", [0.1] * 384, {"title": "test"})
        assert result is False  # Offline returns False

    @pytest.mark.asyncio
    async def test_search_offline(self):
        store = QdrantStore()
        results = await store.search([0.1] * 384, top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_delete_offline(self):
        store = QdrantStore()
        result = await store.delete("doc-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_count_offline(self):
        store = QdrantStore()
        count = await store.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_health_check_offline(self):
        store = QdrantStore(qdrant_url="http://fake:6333")
        result = await store.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_batch_upsert_offline(self):
        store = QdrantStore()
        items = [("d1", [0.1] * 384, {"k": "v"}), ("d2", [0.2] * 384, None)]
        count = await store.upsert_batch(items)
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_by_filter_offline(self):
        store = QdrantStore()
        result = await store.delete_by_filter("source", "test.txt")
        assert result is False

    def test_get_stats(self):
        store = QdrantStore(qdrant_url="http://localhost:6333", collection_name="test_col")
        stats = store.get_stats()
        assert stats["collection"] == "test_col"
        assert stats["dimension"] == 384
        assert stats["available"] is False

    @pytest.mark.asyncio
    async def test_shutdown(self):
        store = QdrantStore()
        await store.shutdown()


# ======================================================================
# OLLAMA EMBEDDINGS (offline fallback to hash)
# ======================================================================


class TestOllamaEmbeddings:
    """Tests for Ollama embedding engine with hash fallback."""

    def test_create_default(self):
        engine = OllamaEmbeddingEngine()
        assert engine.model_name == "nomic-embed-text"
        assert engine.dimensions == 768

    def test_create_custom(self):
        engine = OllamaEmbeddingEngine(model="mxbai-embed-large", dimensions=1024)
        assert engine.model_name == "mxbai-embed-large"
        assert engine.dimensions == 1024

    def test_hash_fallback_embed(self):
        engine = OllamaEmbeddingEngine()
        # embed_text is the sync hash-based fallback
        vec = engine.embed_text("hello world")
        assert len(vec) == 768
        assert all(isinstance(v, float) for v in vec)

    def test_hash_fallback_deterministic(self):
        engine = OllamaEmbeddingEngine()
        v1 = engine.embed_text("same text")
        v2 = engine.embed_text("same text")
        assert v1 == v2

    def test_hash_fallback_different_texts(self):
        engine = OllamaEmbeddingEngine()
        v1 = engine.embed_text("hello")
        v2 = engine.embed_text("world")
        assert v1 != v2

    def test_hash_batch(self):
        engine = OllamaEmbeddingEngine()
        vecs = engine.embed_batch(["a", "b", "c"])
        assert len(vecs) == 3
        assert all(len(v) == 768 for v in vecs)

    @pytest.mark.asyncio
    async def test_async_embed_fallback(self):
        engine = OllamaEmbeddingEngine()
        # Will fall back to hash since no Ollama running
        vec = await engine.embed_text_async("test embedding")
        assert len(vec) == 768
        assert all(isinstance(v, float) for v in vec)

    @pytest.mark.asyncio
    async def test_async_batch_fallback(self):
        engine = OllamaEmbeddingEngine()
        vecs = await engine.embed_batch_async(["text1", "text2"])
        assert len(vecs) == 2
        assert all(len(v) == 768 for v in vecs)

    @pytest.mark.asyncio
    async def test_async_batch_empty(self):
        engine = OllamaEmbeddingEngine()
        vecs = await engine.embed_batch_async([])
        assert vecs == []

    @pytest.mark.asyncio
    async def test_close(self):
        engine = OllamaEmbeddingEngine()
        await engine.close()

    def test_is_available_default(self):
        engine = OllamaEmbeddingEngine()
        assert engine.is_available is False  # Not checked yet


# ======================================================================
# VECTOR RETRIEVER (integrated — offline mode)
# ======================================================================


class TestVectorRetriever:
    """Tests for the production vector retriever (offline mode)."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        retriever = VectorRetriever()
        await retriever.initialize()
        # Should not crash even with no Qdrant/Redis

    @pytest.mark.asyncio
    async def test_search_empty(self):
        retriever = VectorRetriever()
        results = await retriever.search("any query")
        assert results == []  # No Qdrant = no results

    @pytest.mark.asyncio
    async def test_index_document_offline(self):
        retriever = VectorRetriever()
        result = await retriever.index_document("doc-1", "some content", {"source": "test.txt"})
        assert result is False  # Qdrant offline

    @pytest.mark.asyncio
    async def test_index_batch_offline(self):
        retriever = VectorRetriever()
        items = [
            ("d1", "content 1", {"source": "a.txt"}),
            ("d2", "content 2", {"source": "b.txt"}),
        ]
        count = await retriever.index_batch(items)
        assert count == 0  # Qdrant offline

    @pytest.mark.asyncio
    async def test_index_batch_empty(self):
        retriever = VectorRetriever()
        count = await retriever.index_batch([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_document(self):
        retriever = VectorRetriever()
        result = await retriever.delete_document("doc-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_source(self):
        retriever = VectorRetriever()
        result = await retriever.delete_by_source("test.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_stats(self):
        retriever = VectorRetriever()
        stats = retriever.get_stats()
        assert stats["searches"] == 0
        assert stats["cache_hits"] == 0
        assert "qdrant" in stats
        assert "cache" in stats
        assert "embedder" in stats

    @pytest.mark.asyncio
    async def test_shutdown(self):
        retriever = VectorRetriever()
        await retriever.shutdown()


# ======================================================================
# INTEGRATION TESTS (cross-module)
# ======================================================================


class TestPhase19Integration:
    """Integration tests combining Phase 19 components."""

    @pytest.mark.asyncio
    async def test_ollama_complete_and_track(self):
        from ai.token_tracker import TokenTracker

        provider = OllamaProvider()
        tracker = TokenTracker()
        req = AIRequest(messages=[AIMessage(role="user", content="integrate")])
        resp = await provider.complete(req)
        tracker.record(
            provider="ollama",
            model=resp.model,
            prompt_tokens=10,
            completion_tokens=resp.tokens_used,
        )
        total = tracker.get_total()
        assert total.total_tokens > 0

    @pytest.mark.asyncio
    async def test_redis_cache_with_retriever(self):
        cache = RedisCache(prefix="test:")
        await cache.set("vsearch:test:5", [{"content": "cached", "score": 0.9}])
        result = await cache.get("vsearch:test:5")
        assert result is not None
        assert result[0]["content"] == "cached"

    @pytest.mark.asyncio
    async def test_gemini_with_system_prompt(self):
        provider = GeminiProvider()
        req = AIRequest(
            messages=[AIMessage(role="user", content="test")],
            system_prompt="Be brief.",
            temperature=0.5,
            max_tokens=100,
        )
        resp = await provider.complete(req)
        assert resp.provider == "gemini"

    @pytest.mark.asyncio
    async def test_embedding_vector_roundtrip(self):
        embedder = OllamaEmbeddingEngine(dimensions=128)
        text = "The quick brown fox jumps over the lazy dog"
        vec = await embedder.embed_text_async(text)
        assert len(vec) == 128
        # Verify unit vector (approximately)
        import math

        magnitude = math.sqrt(sum(v * v for v in vec))
        assert abs(magnitude - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_postgres_backend_interface(self):
        backend = PostgresBackend()
        # Verify it implements the full interface without errors
        doc = DocumentRecord(
            doc_id="pg-test",
            title="PG Test",
            content="PostgreSQL test document",
            doc_type="text",
            tags=["test", "pg"],
            metadata={"phase": 19},
        )
        await backend.save_document(doc)
        await backend.get_document("pg-test")
        await backend.list_documents(doc_type="text")
        await backend.search_documents("PostgreSQL")
        await backend.delete_document("pg-test")

    @pytest.mark.asyncio
    async def test_full_rag_pipeline_offline(self):
        """Test full RAG pipeline in offline mode — no crashes."""
        retriever = VectorRetriever()
        await retriever.initialize()

        # Index (will fail gracefully)
        await retriever.index_document("d1", "AI is transforming the world")
        await retriever.index_batch(
            [
                ("d2", "Machine learning is a subset of AI", None),
                ("d3", "Deep learning uses neural networks", {"source": "ml.txt"}),
            ]
        )

        # Search (empty results in offline mode)
        results = await retriever.search("artificial intelligence")
        assert isinstance(results, list)

        # Stats
        stats = retriever.get_stats()
        assert stats["searches"] == 1

        await retriever.shutdown()
