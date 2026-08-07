"""Unit tests for the Qdrant adapter mock."""

import pytest

from sona_memory.infrastructure.qdrant_adapter import PointStruct, QdrantAdapter


class TestQdrantBasicOps:
    """Tests for basic upsert/get/delete operations."""

    @pytest.mark.asyncio
    async def test_create_collection(self) -> None:
        qdrant = QdrantAdapter()
        await qdrant.create_collection("test", vector_size=128)
        assert await qdrant.count("test") == 0

    @pytest.mark.asyncio
    async def test_upsert_single(self) -> None:
        qdrant = QdrantAdapter()
        point = PointStruct(id="p1", vector=[0.5] * 128, payload={"key": "val"})
        count = await qdrant.upsert("coll", [point])
        assert count == 1

    @pytest.mark.asyncio
    async def test_upsert_multiple(self) -> None:
        qdrant = QdrantAdapter()
        points = [PointStruct(id=f"p{i}", vector=[float(i) / 10] * 128) for i in range(5)]
        count = await qdrant.upsert("coll", points)
        assert count == 5
        assert await qdrant.count("coll") == 5

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self) -> None:
        qdrant = QdrantAdapter()
        p1 = PointStruct(id="p1", vector=[0.1] * 128, payload={"v": 1})
        await qdrant.upsert("coll", [p1])
        p1_updated = PointStruct(id="p1", vector=[0.9] * 128, payload={"v": 2})
        await qdrant.upsert("coll", [p1_updated])
        assert await qdrant.count("coll") == 1
        result = await qdrant.get("coll", "p1")
        assert result is not None
        assert result.payload["v"] == 2

    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        qdrant = QdrantAdapter()
        point = PointStruct(id="p1", vector=[0.5] * 128, payload={"key": "val"})
        await qdrant.upsert("coll", [point])
        result = await qdrant.get("coll", "p1")
        assert result is not None
        assert result.id == "p1"
        assert result.payload == {"key": "val"}

    @pytest.mark.asyncio
    async def test_get_missing(self) -> None:
        qdrant = QdrantAdapter()
        assert await qdrant.get("coll", "no") is None

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        qdrant = QdrantAdapter()
        point = PointStruct(id="p1", vector=[0.5] * 128)
        await qdrant.upsert("coll", [point])
        deleted = await qdrant.delete("coll", ["p1"])
        assert deleted == 1
        assert await qdrant.count("coll") == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        qdrant = QdrantAdapter()
        deleted = await qdrant.delete("coll", ["no"])
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_delete_collection(self) -> None:
        qdrant = QdrantAdapter()
        await qdrant.create_collection("coll")
        assert await qdrant.delete_collection("coll") is True
        assert await qdrant.count("coll") == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection(self) -> None:
        qdrant = QdrantAdapter()
        assert await qdrant.delete_collection("no") is False


class TestQdrantSearch:
    """Tests for vector similarity search."""

    @pytest.mark.asyncio
    async def test_search_finds_similar(self) -> None:
        qdrant = QdrantAdapter()
        # Store a known vector
        point = PointStruct(id="p1", vector=[1.0] + [0.0] * 127)
        await qdrant.upsert("coll", [point])
        # Search with similar vector
        results = await qdrant.search("coll", [1.0] + [0.0] * 127, limit=5)
        assert len(results) == 1
        assert results[0].id == "p1"
        assert results[0].score > 0.9

    @pytest.mark.asyncio
    async def test_search_respects_limit(self) -> None:
        qdrant = QdrantAdapter()
        points = [PointStruct(id=f"p{i}", vector=[float(i)] + [0.0] * 127) for i in range(10)]
        await qdrant.upsert("coll", points)
        results = await qdrant.search("coll", [5.0] + [0.0] * 127, limit=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_score_threshold(self) -> None:
        qdrant = QdrantAdapter()
        # Two orthogonal vectors
        p1 = PointStruct(id="p1", vector=[1.0] + [0.0] * 127)
        p2 = PointStruct(id="p2", vector=[0.0, 1.0] + [0.0] * 126)
        await qdrant.upsert("coll", [p1, p2])
        # Search for p1's direction with high threshold
        results = await qdrant.search("coll", [1.0] + [0.0] * 127, score_threshold=0.9)
        assert len(results) == 1
        assert results[0].id == "p1"

    @pytest.mark.asyncio
    async def test_search_with_filter(self) -> None:
        qdrant = QdrantAdapter()
        p1 = PointStruct(id="p1", vector=[1.0] + [0.0] * 127, payload={"user": "a"})
        p2 = PointStruct(id="p2", vector=[1.0] + [0.0] * 127, payload={"user": "b"})
        await qdrant.upsert("coll", [p1, p2])
        results = await qdrant.search(
            "coll",
            [1.0] + [0.0] * 127,
            filter_conditions={"user": "a"},
        )
        assert len(results) == 1
        assert results[0].id == "p1"

    @pytest.mark.asyncio
    async def test_search_empty_collection(self) -> None:
        qdrant = QdrantAdapter()
        results = await qdrant.search("coll", [1.0] * 128)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_sorted_by_score(self) -> None:
        qdrant = QdrantAdapter()
        p1 = PointStruct(id="close", vector=[0.9, 0.1] + [0.0] * 126)
        p2 = PointStruct(id="far", vector=[0.1, 0.9] + [0.0] * 126)
        await qdrant.upsert("coll", [p1, p2])
        results = await qdrant.search("coll", [1.0, 0.0] + [0.0] * 126)
        assert results[0].id == "close"


class TestQdrantScroll:
    """Tests for scroll operations."""

    @pytest.mark.asyncio
    async def test_scroll_all(self) -> None:
        qdrant = QdrantAdapter()
        points = [PointStruct(id=f"p{i}", vector=[0.0] * 128) for i in range(5)]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", limit=10)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_scroll_with_offset(self) -> None:
        qdrant = QdrantAdapter()
        points = [PointStruct(id=f"p{i}", vector=[0.0] * 128) for i in range(10)]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", limit=5, offset=3)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_scroll_with_filter(self) -> None:
        qdrant = QdrantAdapter()
        points = [
            PointStruct(id=f"p{i}", vector=[0.0] * 128, payload={"type": "a" if i < 3 else "b"})
            for i in range(6)
        ]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", filter_conditions={"type": "a"})
        assert len(results) == 3


class TestQdrantFilter:
    """Tests for filter condition matching."""

    @pytest.mark.asyncio
    async def test_range_filter_gte(self) -> None:
        qdrant = QdrantAdapter()
        points = [
            PointStruct(id=f"p{i}", vector=[0.5] * 128, payload={"score": i * 0.2})
            for i in range(6)
        ]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", filter_conditions={"score": {"$gte": 0.6}})
        assert len(results) == 3  # scores 0.6, 0.8, 1.0

    @pytest.mark.asyncio
    async def test_range_filter_lt(self) -> None:
        qdrant = QdrantAdapter()
        points = [PointStruct(id=f"p{i}", vector=[0.5] * 128, payload={"val": i}) for i in range(5)]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", filter_conditions={"val": {"$lt": 3}})
        assert len(results) == 3  # vals 0, 1, 2

    @pytest.mark.asyncio
    async def test_in_filter(self) -> None:
        qdrant = QdrantAdapter()
        points = [
            PointStruct(id=f"p{i}", vector=[0.5] * 128, payload={"tag": f"t{i}"}) for i in range(5)
        ]
        await qdrant.upsert("coll", points)
        results = await qdrant.scroll("coll", filter_conditions={"tag": {"$in": ["t1", "t3"]}})
        assert len(results) == 2
