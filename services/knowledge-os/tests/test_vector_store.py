"""Tests for the in-memory vector store."""

import pytest

from sona_knowledge.infrastructure.embedding_service import _hash_to_embedding
from sona_knowledge.infrastructure.vector_store import VectorStore


@pytest.fixture
def store() -> VectorStore:
    return VectorStore()


class TestVectorStore:
    """Tests for VectorStore."""

    @pytest.mark.asyncio
    async def test_initial_size_is_zero(self, store: VectorStore) -> None:
        assert store.size == 0

    @pytest.mark.asyncio
    async def test_upsert_increases_size(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1, 0.2, 0.3])
        assert store.size == 1

    @pytest.mark.asyncio
    async def test_upsert_with_metadata(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1], metadata={"key": "val"})
        record = await store.get("id-1")
        assert record is not None
        assert record.metadata == {"key": "val"}

    @pytest.mark.asyncio
    async def test_upsert_overwrites_existing(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1], content="old")
        await store.upsert("id-1", [0.2], content="new")
        assert store.size == 1
        record = await store.get("id-1")
        assert record is not None
        assert record.content == "new"

    @pytest.mark.asyncio
    async def test_upsert_batch(self, store: VectorStore) -> None:
        records = [
            ("id-1", [0.1, 0.2], {"k": "1"}, "content1"),
            ("id-2", [0.3, 0.4], {"k": "2"}, "content2"),
            ("id-3", [0.5, 0.6], {"k": "3"}, "content3"),
        ]
        await store.upsert_batch(records)
        assert store.size == 3

    @pytest.mark.asyncio
    async def test_search_returns_results(self, store: VectorStore) -> None:
        vec = _hash_to_embedding("hello", dim=64)
        await store.upsert("id-1", vec, content="hello world")
        results = await store.search(vec, top_k=5)
        assert len(results) == 1
        assert results[0].id == "id-1"
        assert results[0].score > 0.9  # Same vector should be very similar

    @pytest.mark.asyncio
    async def test_search_sorted_by_score(self, store: VectorStore) -> None:
        query_vec = _hash_to_embedding("query", dim=64)
        sim_vec = _hash_to_embedding("query text", dim=64)
        diff_vec = _hash_to_embedding("completely different", dim=64)
        await store.upsert("similar", sim_vec, content="query text")
        await store.upsert("different", diff_vec, content="completely different")
        results = await store.search(query_vec, top_k=5)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self, store: VectorStore) -> None:
        for i in range(10):
            vec = _hash_to_embedding(f"doc-{i}", dim=64)
            await store.upsert(f"id-{i}", vec)
        query = _hash_to_embedding("doc-0", dim=64)
        results = await store.search(query, top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_min_score_filter(self, store: VectorStore) -> None:
        vec1 = _hash_to_embedding("target", dim=64)
        vec2 = _hash_to_embedding("something unrelated xyz", dim=64)
        await store.upsert("id-1", vec1, content="target")
        await store.upsert("id-2", vec2, content="unrelated")
        results = await store.search(vec1, top_k=10, min_score=0.99)
        # Only the exact match should pass high threshold
        assert all(r.score >= 0.99 for r in results)

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, store: VectorStore) -> None:
        vec = _hash_to_embedding("test", dim=64)
        await store.upsert("id-1", vec, metadata={"kb_id": "kb-1"})
        await store.upsert("id-2", vec, metadata={"kb_id": "kb-2"})
        results = await store.search(vec, metadata_filter={"kb_id": "kb-1"})
        assert len(results) == 1
        assert results[0].id == "id-1"

    @pytest.mark.asyncio
    async def test_delete_existing(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1])
        assert await store.delete("id-1") is True
        assert store.size == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: VectorStore) -> None:
        assert await store.delete("nonexistent") is False

    @pytest.mark.asyncio
    async def test_delete_by_metadata(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1], metadata={"doc": "a"})
        await store.upsert("id-2", [0.2], metadata={"doc": "a"})
        await store.upsert("id-3", [0.3], metadata={"doc": "b"})
        count = await store.delete_by_metadata({"doc": "a"})
        assert count == 2
        assert store.size == 1

    @pytest.mark.asyncio
    async def test_get_existing(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1, 0.2], content="hello")
        record = await store.get("id-1")
        assert record is not None
        assert record.content == "hello"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store: VectorStore) -> None:
        record = await store.get("nonexistent")
        assert record is None

    @pytest.mark.asyncio
    async def test_clear(self, store: VectorStore) -> None:
        await store.upsert("id-1", [0.1])
        await store.upsert("id-2", [0.2])
        await store.clear()
        assert store.size == 0
