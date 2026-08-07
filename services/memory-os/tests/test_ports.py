"""Unit tests for Memory OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest

from sona_memory.application.ports import EmbeddingPort, MemoryStorePort
from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType


class TestMemoryStorePort:
    """Tests for the MemoryStorePort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify MemoryStorePort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MemoryStorePort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = MemoryStorePort.__abstractmethods__
        assert "store" in abstract_methods
        assert "retrieve" in abstract_methods
        assert "consolidate" in abstract_methods
        assert "forget" in abstract_methods
        assert "get_conversation_history" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteMemoryStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return entry.id

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return []

            async def consolidate(self, user_id: str) -> int:
                return 0

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return True

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return []

        store = ConcreteMemoryStore()
        assert isinstance(store, MemoryStorePort)

    @pytest.mark.asyncio
    async def test_store_returns_id(self) -> None:
        """Test that a concrete store() returns a memory ID."""

        class MockStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return f"stored-{entry.id}"

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return []

            async def consolidate(self, user_id: str) -> int:
                return 0

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return True

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return []

        store = MockStore()
        entry = MemoryEntry(
            id="mem-001",
            memory_type=MemoryType.WORKING,
            content="Test memory",
        )
        result = await store.store("user-123", entry)
        assert result == "stored-mem-001"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_retrieve_returns_list(self) -> None:
        """Test that a concrete retrieve() returns a list of entries."""

        class MockStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return entry.id

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return [
                    MemoryEntry(
                        id="mem-001",
                        memory_type=MemoryType.LONG_TERM,
                        content="Relevant memory",
                        importance=0.8,
                    )
                ]

            async def consolidate(self, user_id: str) -> int:
                return 0

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return True

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return []

        store = MockStore()
        query = MemoryQuery(user_id="user-123", query="relevant")
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].content == "Relevant memory"
        assert isinstance(results[0], MemoryEntry)

    @pytest.mark.asyncio
    async def test_consolidate_returns_count(self) -> None:
        """Test that consolidate() returns the number of consolidated memories."""

        class MockStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return entry.id

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return []

            async def consolidate(self, user_id: str) -> int:
                return 3

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return True

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return []

        store = MockStore()
        count = await store.consolidate("user-123")
        assert count == 3
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_forget_returns_bool(self) -> None:
        """Test that forget() returns success status."""

        class MockStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return entry.id

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return []

            async def consolidate(self, user_id: str) -> int:
                return 0

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return memory_id == "mem-001"

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return []

        store = MockStore()
        assert await store.forget("user-123", "mem-001") is True
        assert await store.forget("user-123", "nonexistent") is False

    @pytest.mark.asyncio
    async def test_get_conversation_history_returns_list(self) -> None:
        """Test that get_conversation_history() returns memory entries."""

        class MockStore(MemoryStorePort):
            async def store(self, user_id: str, entry: MemoryEntry) -> str:
                return entry.id

            async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
                return []

            async def consolidate(self, user_id: str) -> int:
                return 0

            async def forget(self, user_id: str, memory_id: str) -> bool:
                return True

            async def get_conversation_history(
                self, session_id: str, limit: int = 50
            ) -> list[MemoryEntry]:
                return [
                    MemoryEntry(
                        id="conv-001",
                        memory_type=MemoryType.WORKING,
                        content="Hello, how are you?",
                    ),
                    MemoryEntry(
                        id="conv-002",
                        memory_type=MemoryType.WORKING,
                        content="I'm doing well, thanks!",
                    ),
                ]

        store = MockStore()
        history = await store.get_conversation_history("session-abc", limit=10)
        assert len(history) == 2
        assert all(isinstance(e, MemoryEntry) for e in history)


class TestEmbeddingPort:
    """Tests for the EmbeddingPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify EmbeddingPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EmbeddingPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = EmbeddingPort.__abstractmethods__
        assert "embed" in abstract_methods
        assert "embed_batch" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteEmbedder(EmbeddingPort):
            async def embed(self, text: str) -> list[float]:
                return [0.0] * 384

            async def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * 384 for _ in texts]

        embedder = ConcreteEmbedder()
        assert isinstance(embedder, EmbeddingPort)

    @pytest.mark.asyncio
    async def test_embed_returns_vector(self) -> None:
        """Test that embed() returns a float vector."""

        class MockEmbedder(EmbeddingPort):
            async def embed(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3] * 128  # 384-dim vector

            async def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1, 0.2, 0.3] * 128 for _ in texts]

        embedder = MockEmbedder()
        result = await embedder.embed("test text")
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(isinstance(v, float) for v in result)

    @pytest.mark.asyncio
    async def test_embed_batch_returns_vectors(self) -> None:
        """Test that embed_batch() returns a list of vectors."""

        class MockEmbedder(EmbeddingPort):
            async def embed(self, text: str) -> list[float]:
                return [0.5] * 384

            async def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.5] * 384 for _ in texts]

        embedder = MockEmbedder()
        texts = ["hello", "world", "test"]
        results = await embedder.embed_batch(texts)
        assert len(results) == 3
        assert all(len(v) == 384 for v in results)
        assert all(isinstance(v, list) for v in results)
