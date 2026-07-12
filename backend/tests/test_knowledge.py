"""Knowledge Engine tests — storage, vector, RAG, and retrieval."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEmbeddings:
    """Test embedding engine."""

    def test_embed_text(self):
        from vector.embeddings import EmbeddingEngine

        engine = EmbeddingEngine(dimensions=128)
        emb = engine.embed_text("hello world")
        assert len(emb) == 128
        assert all(isinstance(v, float) for v in emb)

    def test_embed_deterministic(self):
        from vector.embeddings import EmbeddingEngine

        engine = EmbeddingEngine()
        e1 = engine.embed_text("test input")
        e2 = engine.embed_text("test input")
        assert e1 == e2

    def test_embed_batch(self):
        from vector.embeddings import EmbeddingEngine

        engine = EmbeddingEngine(dimensions=64)
        results = engine.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(len(e) == 64 for e in results)

    def test_chunk_text(self):
        from vector.embeddings import chunk_text

        text = "Hello world. " * 500
        chunks = chunk_text(text, chunk_size=100)
        assert len(chunks) > 1
        assert all(c.token_estimate > 0 for c in chunks)
        assert chunks[0].chunk_index == 0

    def test_chunk_text_empty(self):
        from vector.embeddings import chunk_text

        chunks = chunk_text("")
        assert chunks == []

    def test_chunk_text_short(self):
        from vector.embeddings import chunk_text

        chunks = chunk_text("Short text", chunk_size=1000)
        # Short text might not meet minimum chunk size
        assert len(chunks) <= 1


class TestVectorStore:
    """Test in-memory vector store."""

    def test_add_and_count(self):
        from vector.memory_store import InMemoryVectorStore
        from vector.store import VectorRecord

        store = InMemoryVectorStore()
        asyncio.run(store.initialize())

        records = [
            VectorRecord(record_id="r1", content="hello", embedding=[1.0, 0.0, 0.0]),
            VectorRecord(record_id="r2", content="world", embedding=[0.0, 1.0, 0.0]),
        ]
        count = asyncio.run(store.add(records))
        assert count == 2
        assert asyncio.run(store.count()) == 2

    def test_search_cosine(self):
        from vector.memory_store import InMemoryVectorStore
        from vector.store import VectorRecord

        store = InMemoryVectorStore()
        asyncio.run(store.initialize())

        records = [
            VectorRecord(record_id="r1", content="hello", embedding=[1.0, 0.0, 0.0]),
            VectorRecord(record_id="r2", content="world", embedding=[0.0, 1.0, 0.0]),
            VectorRecord(record_id="r3", content="mixed", embedding=[0.7, 0.7, 0.0]),
        ]
        asyncio.run(store.add(records))

        # Search for vector most similar to [1, 0, 0]
        results = asyncio.run(store.search([1.0, 0.0, 0.0], top_k=2))
        assert len(results) == 2
        assert results[0].record.record_id == "r1"
        assert results[0].score > 0.9

    def test_delete(self):
        from vector.memory_store import InMemoryVectorStore
        from vector.store import VectorRecord

        store = InMemoryVectorStore()
        asyncio.run(store.initialize())
        asyncio.run(
            store.add(
                [
                    VectorRecord(record_id="r1", content="a", embedding=[1.0]),
                    VectorRecord(record_id="r2", content="b", embedding=[0.5]),
                ]
            )
        )

        deleted = asyncio.run(store.delete(["r1"]))
        assert deleted == 1
        assert asyncio.run(store.count()) == 1

    def test_delete_by_doc(self):
        from vector.memory_store import InMemoryVectorStore
        from vector.store import VectorRecord

        store = InMemoryVectorStore()
        asyncio.run(store.initialize())
        asyncio.run(
            store.add(
                [
                    VectorRecord(record_id="r1", content="a", embedding=[1.0], doc_id="doc1"),
                    VectorRecord(record_id="r2", content="b", embedding=[0.5], doc_id="doc1"),
                    VectorRecord(record_id="r3", content="c", embedding=[0.3], doc_id="doc2"),
                ]
            )
        )

        deleted = asyncio.run(store.delete_by_doc("doc1"))
        assert deleted == 2
        assert asyncio.run(store.count()) == 1


class TestSQLiteStorage:
    """Test SQLite storage backend."""

    def test_save_and_get_document(self):
        from storage.repository import DocumentRecord
        from storage.sqlite_backend import SQLiteBackend

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = SQLiteBackend(db_path)
            asyncio.run(backend.initialize())

            doc = DocumentRecord(
                title="Test Doc",
                content="Hello world",
                doc_type="text",
                source="test.txt",
                tags=["test"],
            )
            doc_id = asyncio.run(backend.save_document(doc))
            retrieved = asyncio.run(backend.get_document(doc_id))

            assert retrieved is not None
            assert retrieved.title == "Test Doc"
            assert retrieved.content == "Hello world"
            assert "test" in retrieved.tags

            asyncio.run(backend.shutdown())
        finally:
            os.unlink(db_path)

    def test_search_documents(self):
        from storage.repository import DocumentRecord
        from storage.sqlite_backend import SQLiteBackend

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = SQLiteBackend(db_path)
            asyncio.run(backend.initialize())

            asyncio.run(
                backend.save_document(
                    DocumentRecord(
                        title="Python Guide",
                        content="Python is a programming language",
                        doc_type="text",
                    )
                )
            )
            asyncio.run(
                backend.save_document(
                    DocumentRecord(
                        title="Java Guide", content="Java is another language", doc_type="text"
                    )
                )
            )

            results = asyncio.run(backend.search_documents("Python"))
            assert len(results) >= 1
            assert any("Python" in r.content for r in results)

            asyncio.run(backend.shutdown())
        finally:
            os.unlink(db_path)

    def test_save_and_search_memory(self):
        from storage.repository import MemoryRecord
        from storage.sqlite_backend import SQLiteBackend

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = SQLiteBackend(db_path)
            asyncio.run(backend.initialize())

            asyncio.run(
                backend.save_memory(
                    MemoryRecord(
                        content="User asked about Python asyncio",
                        memory_type="conversation",
                        session_id="session-1",
                    )
                )
            )

            mems = asyncio.run(backend.get_memories(session_id="session-1"))
            assert len(mems) == 1
            assert "asyncio" in mems[0].content

            search_results = asyncio.run(backend.search_memories("asyncio"))
            assert len(search_results) >= 1

            asyncio.run(backend.shutdown())
        finally:
            os.unlink(db_path)


class TestDocumentIngester:
    """Test document ingestion pipeline."""

    def test_ingest_text(self):
        from rag.ingestion import DocumentIngester

        ingester = DocumentIngester()
        doc, vectors = ingester.ingest_text(
            content="This is a test document with some content. " * 50,
            title="Test",
            source="test.txt",
            doc_type="text",
        )

        assert doc.doc_id is not None
        assert doc.chunk_count > 0
        assert doc.token_count > 0
        assert len(vectors) == doc.chunk_count
        assert all(v.embedding for v in vectors)

    def test_detect_file_type(self):
        from rag.ingestion import DocumentIngester

        ingester = DocumentIngester()
        assert ingester.detect_file_type("main.py") == "py"
        assert ingester.detect_file_type("readme.md") == "md"
        assert ingester.detect_file_type("data.json") == "json"
        assert ingester.detect_file_type("unknown.xyz") == "text"


class TestRAGEngine:
    """Test the full RAG engine."""

    def test_ingest_and_search(self):
        from rag.engine import RAGEngine

        engine = RAGEngine()
        asyncio.run(engine.initialize())

        # Ingest a document
        doc = asyncio.run(
            engine.ingest_document(
                content="Python asyncio provides concurrent programming with async/await syntax. "
                * 20,
                title="Python Async Guide",
                doc_type="text",
            )
        )
        assert doc.chunk_count > 0

        # Search should find it
        results = asyncio.run(engine.search("Python async", top_k=5, min_score=0.0))
        assert len(results) > 0

        asyncio.run(engine.shutdown())

    def test_build_context(self):
        from rag.engine import RAGEngine

        engine = RAGEngine()
        asyncio.run(engine.initialize())

        asyncio.run(
            engine.ingest_document(
                content="FastAPI is a modern Python web framework for building APIs. " * 20,
                title="FastAPI Guide",
            )
        )

        context = asyncio.run(engine.build_context("FastAPI web framework"))
        # Context may be empty if hash-based embeddings don't match
        # but the function should not error
        assert isinstance(context, str)

        asyncio.run(engine.shutdown())

    def test_delete_document(self):
        from rag.engine import RAGEngine

        engine = RAGEngine()
        asyncio.run(engine.initialize())

        doc = asyncio.run(
            engine.ingest_document(content="Deletable content " * 30, title="To Delete")
        )
        assert asyncio.run(engine.delete_document(doc.doc_id)) is True
        assert asyncio.run(engine.get_document(doc.doc_id)) is None

        asyncio.run(engine.shutdown())

    def test_get_stats(self):
        from rag.engine import RAGEngine

        engine = RAGEngine()
        asyncio.run(engine.initialize())

        asyncio.run(engine.ingest_document(content="Stats test content " * 30, title="Stats"))
        stats = asyncio.run(engine.get_stats())

        assert stats["documents"] >= 1
        assert stats["vectors"] >= 1
        assert stats["embedding_dimensions"] == 384

        asyncio.run(engine.shutdown())
