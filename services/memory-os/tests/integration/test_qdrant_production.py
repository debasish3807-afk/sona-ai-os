"""Integration tests for production Qdrant adapter.

These tests require a running Qdrant instance.
They are automatically skipped if Qdrant is not available.
"""

import pytest

from sona_memory.infrastructure.qdrant_production import (
    QdrantPoint,
    QdrantProductionAdapter,
)


def _qdrant_available() -> bool:
    """Check if Qdrant is available for testing."""
    try:
        import httpx

        response = httpx.get("http://localhost:6333/healthz", timeout=2.0)
        return response.status_code == 200
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(not _qdrant_available(), reason="Qdrant not running")


class TestQdrantProductionAdapter:
    """Integration tests for QdrantProductionAdapter with real Qdrant."""

    @pytest.fixture
    async def adapter(self) -> QdrantProductionAdapter:
        """Create and connect a production adapter."""
        adapter = QdrantProductionAdapter(
            url="http://localhost:6333",
            collection="test_sona_memories",
            vector_size=4,
            max_retries=1,
            retry_delay=0.1,
        )
        await adapter.connect()
        await adapter.ensure_collection()
        yield adapter  # type: ignore[misc]
        await adapter.disconnect()

    async def test_connect(self, adapter: QdrantProductionAdapter) -> None:
        """Test that connection is established."""
        assert adapter.is_connected

    async def test_upsert_and_search(self, adapter: QdrantProductionAdapter) -> None:
        """Test upserting points and searching by vector similarity."""
        points = [
            QdrantPoint(
                id="p1",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={"type": "fact"},
            ),
            QdrantPoint(
                id="p2",
                vector=[0.0, 1.0, 0.0, 0.0],
                payload={"type": "episode"},
            ),
        ]
        await adapter.upsert(points)

        # Search for vector closest to p1
        results = await adapter.search(vector=[0.9, 0.1, 0.0, 0.0], limit=2)
        assert len(results) >= 1
        # First result should be p1 (most similar)
        top_point, top_score = results[0]
        assert top_point.id == "p1"
        assert top_score > 0.5

        # Cleanup
        await adapter.delete(["p1", "p2"])

    async def test_filter_search(self, adapter: QdrantProductionAdapter) -> None:
        """Test searching with payload filter."""
        points = [
            QdrantPoint(
                id="f1",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={"category": "work"},
            ),
            QdrantPoint(
                id="f2",
                vector=[0.9, 0.1, 0.0, 0.0],
                payload={"category": "personal"},
            ),
        ]
        await adapter.upsert(points)

        # Search with filter - only personal category
        results = await adapter.search(
            vector=[1.0, 0.0, 0.0, 0.0],
            limit=5,
            filter_payload={"category": "personal"},
        )
        assert len(results) >= 1
        assert results[0][0].payload["category"] == "personal"

        await adapter.delete(["f1", "f2"])

    async def test_delete(self, adapter: QdrantProductionAdapter) -> None:
        """Test deleting points."""
        points = [
            QdrantPoint(
                id="d1",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={},
            ),
        ]
        await adapter.upsert(points)
        await adapter.delete(["d1"])
        # Search should return empty or not include d1
        results = await adapter.search(vector=[1.0, 0.0, 0.0, 0.0], limit=5)
        point_ids = [p.id for p, _ in results]
        assert "d1" not in point_ids


class TestQdrantProductionAdapterFallback:
    """Tests for fallback behavior when Qdrant is unavailable."""

    async def test_fallback_to_mock(self) -> None:
        """Adapter falls back to mock when Qdrant is unreachable."""
        adapter = QdrantProductionAdapter(
            url="http://nonexistent-host:9999",
            collection="fallback_test",
            vector_size=4,
            max_retries=1,
            retry_delay=0.01,
        )
        await adapter.connect()
        assert adapter.is_connected
        assert not adapter.is_using_real_qdrant

        # Operations should work via mock
        await adapter.ensure_collection()
        points = [
            QdrantPoint(
                id="mock1",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={"test": True},
            ),
        ]
        await adapter.upsert(points)
        count = await adapter.count()
        assert count >= 1
        await adapter.disconnect()
