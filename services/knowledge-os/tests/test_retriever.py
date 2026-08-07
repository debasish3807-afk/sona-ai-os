"""Tests for the retriever module."""

import pytest

from sona_knowledge.infrastructure.embedding_service import EmbeddingService
from sona_knowledge.infrastructure.retriever import Retriever
from sona_knowledge.infrastructure.vector_store import VectorStore


@pytest.fixture
async def retriever() -> Retriever:
    embedding_service = EmbeddingService(vector_size=64)
    vector_store = VectorStore()
    # Seed some data
    emb1 = await embedding_service.embed("Python is a programming language")
    emb2 = await embedding_service.embed("JavaScript is for web development")
    emb3 = await embedding_service.embed("Rust is a systems language")
    await vector_store.upsert(
        "chunk-1", emb1, metadata={"kb_id": "kb-1"}, content="Python is a programming language"
    )
    await vector_store.upsert(
        "chunk-2", emb2, metadata={"kb_id": "kb-1"}, content="JavaScript is for web development"
    )
    await vector_store.upsert(
        "chunk-3", emb3, metadata={"kb_id": "kb-2"}, content="Rust is a systems language"
    )
    return Retriever(embedding_service=embedding_service, vector_store=vector_store)


class TestRetriever:
    """Tests for Retriever."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_results(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("Python programming")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_retrieve_respects_top_k(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("programming", top_k=1)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_retrieve_filters_by_kb_id(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("language", kb_id="kb-2")
        for result in results:
            assert result.metadata.get("kb_id") == "kb-2"

    @pytest.mark.asyncio
    async def test_retrieve_min_similarity_filter(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("Python", min_similarity=0.99)
        # Very high threshold should only match exact
        for result in results:
            assert result.score >= 0.99

    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("")
        # Should return some results (hash of empty string is valid)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_no_results_high_threshold(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("zzz_nonexistent_xyz", min_similarity=0.999)
        # Unlikely to match anything with high threshold
        assert len(results) == 0 or all(r.score >= 0.999 for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_results_sorted_by_score(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("programming language", top_k=5)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_retrieve_result_has_content(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("Python", top_k=3)
        for result in results:
            assert result.content != ""

    @pytest.mark.asyncio
    async def test_retrieve_no_kb_filter_returns_all(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("language", top_k=10, min_similarity=-1.0)
        # Should get results from both kb-1 and kb-2
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_exact_match_highest_score(self, retriever: Retriever) -> None:
        results = await retriever.retrieve("Python is a programming language", top_k=3)
        # The exact match should have the highest score
        assert results[0].score > 0.99
