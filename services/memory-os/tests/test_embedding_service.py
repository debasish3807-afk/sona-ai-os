"""Unit tests for the embedding service."""

import pytest

from sona_memory.infrastructure.embedding_service import (
    EMBEDDING_DIM,
    EmbeddingService,
    _hash_to_embedding,
    cosine_similarity,
)


class TestHashToEmbedding:
    """Tests for the deterministic hash embedding function."""

    def test_returns_correct_dimension(self) -> None:
        emb = _hash_to_embedding("hello", 128)
        assert len(emb) == 128

    def test_custom_dimension(self) -> None:
        emb = _hash_to_embedding("hello", 64)
        assert len(emb) == 64

    def test_deterministic(self) -> None:
        emb1 = _hash_to_embedding("test text")
        emb2 = _hash_to_embedding("test text")
        assert emb1 == emb2

    def test_different_texts_different_embeddings(self) -> None:
        emb1 = _hash_to_embedding("hello")
        emb2 = _hash_to_embedding("world")
        assert emb1 != emb2

    def test_unit_vector(self) -> None:
        emb = _hash_to_embedding("normalize test")
        magnitude = sum(x * x for x in emb) ** 0.5
        assert abs(magnitude - 1.0) < 1e-6

    def test_empty_string(self) -> None:
        emb = _hash_to_embedding("")
        assert len(emb) == EMBEDDING_DIM
        magnitude = sum(x * x for x in emb) ** 0.5
        assert abs(magnitude - 1.0) < 1e-6

    def test_long_string(self) -> None:
        emb = _hash_to_embedding("a" * 10000)
        assert len(emb) == EMBEDDING_DIM

    def test_values_between_minus_one_and_one(self) -> None:
        emb = _hash_to_embedding("range test")
        for v in emb:
            assert -1.0 <= v <= 1.0


class TestCosineSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_vectors(self) -> None:
        v = [0.5, 0.5, 0.5, 0.5]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_opposite_vectors(self) -> None:
        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v1, v2) - (-1.0)) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        assert abs(cosine_similarity(v1, v2)) < 1e-6

    def test_similar_vectors(self) -> None:
        v1 = [1.0, 1.0, 0.0]
        v2 = [1.0, 0.9, 0.1]
        sim = cosine_similarity(v1, v2)
        assert sim > 0.9

    def test_different_lengths_returns_zero(self) -> None:
        v1 = [1.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        assert cosine_similarity(v1, v2) == 0.0

    def test_zero_vector_returns_zero(self) -> None:
        v1 = [0.0, 0.0, 0.0]
        v2 = [1.0, 1.0, 1.0]
        assert cosine_similarity(v1, v2) == 0.0

    def test_symmetry(self) -> None:
        v1 = [0.3, 0.7, 0.1]
        v2 = [0.8, 0.2, 0.5]
        assert abs(cosine_similarity(v1, v2) - cosine_similarity(v2, v1)) < 1e-10

    def test_hash_embeddings_self_similarity(self) -> None:
        emb = _hash_to_embedding("self similar")
        assert abs(cosine_similarity(emb, emb) - 1.0) < 1e-6

    def test_hash_embeddings_different_texts(self) -> None:
        emb1 = _hash_to_embedding("cat")
        emb2 = _hash_to_embedding("dog")
        sim = cosine_similarity(emb1, emb2)
        # Different texts should not be identical
        assert sim < 1.0


class TestEmbeddingService:
    """Tests for the EmbeddingService class."""

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dim(self) -> None:
        svc = EmbeddingService(dim=128)
        emb = await svc.embed("hello world")
        assert len(emb) == 128

    @pytest.mark.asyncio
    async def test_embed_custom_dim(self) -> None:
        svc = EmbeddingService(dim=256)
        emb = await svc.embed("test")
        assert len(emb) == 256

    @pytest.mark.asyncio
    async def test_embed_deterministic(self) -> None:
        svc = EmbeddingService()
        emb1 = await svc.embed("same text")
        emb2 = await svc.embed("same text")
        assert emb1 == emb2

    @pytest.mark.asyncio
    async def test_embed_batch(self) -> None:
        svc = EmbeddingService(dim=64)
        texts = ["hello", "world", "foo"]
        results = await svc.embed_batch(texts)
        assert len(results) == 3
        assert all(len(v) == 64 for v in results)

    @pytest.mark.asyncio
    async def test_embed_batch_consistency(self) -> None:
        svc = EmbeddingService()
        single = await svc.embed("hello")
        batch = await svc.embed_batch(["hello"])
        assert single == batch[0]

    @pytest.mark.asyncio
    async def test_embed_batch_empty(self) -> None:
        svc = EmbeddingService()
        results = await svc.embed_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_dimension_property(self) -> None:
        svc = EmbeddingService(dim=512)
        assert svc.dimension == 512
