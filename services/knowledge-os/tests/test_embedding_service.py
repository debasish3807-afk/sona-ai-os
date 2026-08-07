"""Tests for the embedding service."""

import pytest

from sona_knowledge.infrastructure.embedding_service import (
    EmbeddingService,
    _hash_to_embedding,
    cosine_similarity,
)


@pytest.fixture
def service() -> EmbeddingService:
    return EmbeddingService(vector_size=384)


class TestHashToEmbedding:
    """Tests for _hash_to_embedding function."""

    def test_correct_dimension(self) -> None:
        emb = _hash_to_embedding("test", dim=384)
        assert len(emb) == 384

    def test_custom_dimension(self) -> None:
        emb = _hash_to_embedding("test", dim=128)
        assert len(emb) == 128

    def test_deterministic(self) -> None:
        emb1 = _hash_to_embedding("hello world")
        emb2 = _hash_to_embedding("hello world")
        assert emb1 == emb2

    def test_different_texts_different_embeddings(self) -> None:
        emb1 = _hash_to_embedding("hello")
        emb2 = _hash_to_embedding("world")
        assert emb1 != emb2

    def test_normalized_to_unit_vector(self) -> None:
        emb = _hash_to_embedding("test text")
        import math

        magnitude = math.sqrt(sum(x * x for x in emb))
        assert abs(magnitude - 1.0) < 1e-6

    def test_values_in_range(self) -> None:
        emb = _hash_to_embedding("some text")
        for val in emb:
            assert -1.0 <= val <= 1.0

    def test_empty_string(self) -> None:
        emb = _hash_to_embedding("")
        assert len(emb) == 384
        # Should still be normalized
        import math

        magnitude = math.sqrt(sum(x * x for x in emb))
        assert abs(magnitude - 1.0) < 1e-6


class TestCosineSimilarity:
    """Tests for cosine_similarity function."""

    def test_identical_vectors(self) -> None:
        vec = [0.5, 0.5, 0.5, 0.5]
        assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_different_lengths_returns_zero(self) -> None:
        a = [1.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert cosine_similarity(a, b) == 0.0

    def test_zero_vector_returns_zero(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert cosine_similarity(a, b) == 0.0

    def test_same_text_identical_similarity(self) -> None:
        emb1 = _hash_to_embedding("Python programming language")
        emb2 = _hash_to_embedding("Python programming language")
        sim = cosine_similarity(emb1, emb2)
        assert abs(sim - 1.0) < 1e-6

    def test_different_texts_not_identical(self) -> None:
        emb1 = _hash_to_embedding("Python programming language")
        emb2 = _hash_to_embedding("Python programming language features")
        sim = cosine_similarity(emb1, emb2)
        # Different texts should not be identical
        assert sim < 1.0


class TestEmbeddingService:
    """Tests for EmbeddingService class."""

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimension(self, service: EmbeddingService) -> None:
        emb = await service.embed("test")
        assert len(emb) == 384

    @pytest.mark.asyncio
    async def test_embed_is_deterministic(self, service: EmbeddingService) -> None:
        emb1 = await service.embed("hello")
        emb2 = await service.embed("hello")
        assert emb1 == emb2

    @pytest.mark.asyncio
    async def test_embed_batch(self, service: EmbeddingService) -> None:
        texts = ["hello", "world", "foo"]
        embeddings = await service.embed_batch(texts)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384

    @pytest.mark.asyncio
    async def test_embed_batch_empty(self, service: EmbeddingService) -> None:
        embeddings = await service.embed_batch([])
        assert embeddings == []

    @pytest.mark.asyncio
    async def test_dimension_property(self, service: EmbeddingService) -> None:
        assert service.dimension == 384

    @pytest.mark.asyncio
    async def test_custom_dimension_service(self) -> None:
        service = EmbeddingService(vector_size=64)
        emb = await service.embed("test")
        assert len(emb) == 64
        assert service.dimension == 64
