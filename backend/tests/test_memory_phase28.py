"""Tests for Phase 28: Knowledge Graph, Memory Ranker, Compressor, Context, Recall."""

import time

import pytest

from memory.compressor import MemoryCompressor
from memory.concrete_types import (
    ConcreteConversationMemory,
    ConcreteEpisodicMemory,
    ConcreteKnowledgeMemory,
    ConcreteSemanticMemory,
)
from memory.context_assembler import ContextAssembler
from memory.knowledge_graph import KnowledgeGraph


class TestKnowledgeGraph:
    def test_add_entity(self):
        g = KnowledgeGraph()
        e = g.add_entity("Python", "language")
        assert e.id is not None
        assert e.name == "Python"
        assert g.get_entity(e.id) is not None

    def test_add_relation(self):
        g = KnowledgeGraph()
        e1 = g.add_entity("Python", "language")
        e2 = g.add_entity("Django", "framework")
        r = g.add_relation(e1.id, e2.id, "used_by")
        assert r.id is not None
        rels = g.get_relations(e1.id)
        assert len(rels) == 1

    def test_search_entities(self):
        g = KnowledgeGraph()
        g.add_entity("Python", "language")
        g.add_entity("JavaScript", "language")
        g.add_entity("React", "framework")
        results = g.search_entities("python")
        assert len(results) == 1
        assert results[0].name == "Python"

    def test_traverse(self):
        g = KnowledgeGraph()
        e1 = g.add_entity("A", "type")
        e2 = g.add_entity("B", "type")
        e3 = g.add_entity("C", "type")
        g.add_relation(e1.id, e2.id, "connects")
        g.add_relation(e2.id, e3.id, "connects")
        path = g.traverse(e1.id, depth=2)
        assert len(path) >= 2

    def test_stats(self):
        g = KnowledgeGraph()
        g.add_entity("X", "a")
        g.add_entity("Y", "b")
        stats = g.get_stats()
        assert stats["entities"] == 2

    def test_clear(self):
        g = KnowledgeGraph()
        g.add_entity("Tmp", "t")
        g.clear()
        assert g.get_stats()["entities"] == 0


class TestMemoryRanker:
    def test_score(self):
        from memory.ranker import MemoryRanker

        ranker = MemoryRanker()

        class FakeEntry:
            importance = 0.8
            accessed_at = time.time()
            access_count = 10

        score = ranker.score(FakeEntry(), query_relevance=0.5)
        assert 0.0 < score <= 1.0

    def test_rank(self):
        from memory.ranker import MemoryRanker

        ranker = MemoryRanker()

        class FakeEntry:
            def __init__(self, imp):
                self.importance = imp
                self.accessed_at = time.time()
                self.access_count = 0

        entries = [FakeEntry(0.1), FakeEntry(0.9), FakeEntry(0.5)]
        ranked = ranker.rank(entries, "test", top_k=2)
        assert len(ranked) == 2
        assert ranked[0][1] >= ranked[1][1]


class TestMemoryCompressor:
    def test_deduplicate(self):
        compressor = MemoryCompressor()

        class FakeEntry:
            def __init__(self, content):
                self.content = content

        entries = [FakeEntry("hello world"), FakeEntry("hello world"), FakeEntry("different")]
        deduped = compressor.deduplicate(entries)
        assert len(deduped) == 2

    def test_archive(self):
        compressor = MemoryCompressor()

        class FakeEntry:
            def __init__(self, created_at):
                self.created_at = created_at

        old = FakeEntry(time.time() - 9999999)
        new = FakeEntry(time.time())
        active = compressor.archive([old, new], max_age_days=1)
        assert len(active) == 1


class TestContextAssembler:
    def test_build_empty(self):
        ca = ContextAssembler()
        result = ca.build()
        assert "## Context" in result

    def test_build_with_conversation(self):
        ca = ContextAssembler()
        conv = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        result = ca.build(recent_conversations=conv)
        assert "Hello" in result
        assert "Hi" in result

    def test_build_with_memories(self):
        ca = ContextAssembler()
        mems = [{"content": "The sky is blue"}]
        result = ca.build(semantic_memories=mems)
        assert "sky is blue" in result

    def test_estimate_tokens(self):
        ca = ContextAssembler()
        assert ca.estimate_tokens("hello") == 1
        assert ca.estimate_tokens("x" * 100) == 25


class TestConcreteSemanticMemory:
    @pytest.mark.asyncio
    async def test_store_and_search(self):
        m = ConcreteSemanticMemory(":memory:")
        await m.initialize()
        eid = await m.store(
            "Python is a programming language",
            entity_type="language",
            entity_name="Python",
            tags=["programming"],
        )
        assert eid is not None
        results = await m.search("Python")
        assert len(results) >= 1
        assert results[0]["entity_name"] == "Python"

    @pytest.mark.asyncio
    async def test_count(self):
        m = ConcreteSemanticMemory(":memory:")
        await m.initialize()
        await m.store("test data")
        c = await m.count()
        assert c >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        m = ConcreteSemanticMemory(":memory:")
        await m.initialize()
        results = await m.search("nonexistent_xyz_999")
        assert len(results) == 0


class TestConcreteEpisodicMemory:
    @pytest.mark.asyncio
    async def test_store_and_search(self):
        m = ConcreteEpisodicMemory(":memory:")
        await m.initialize()
        eid = await m.store(
            "Went for a walk", event_type="activity", location="park", participants=["Alice"]
        )
        assert eid is not None
        results = await m.search("walk")
        assert len(results) >= 1
        assert results[0]["location"] == "park"


class TestConcreteKnowledgeMemory:
    @pytest.mark.asyncio
    async def test_store_and_search(self):
        m = ConcreteKnowledgeMemory(":memory:")
        await m.initialize()
        eid = await m.store("E=mc^2", domain="physics", source="Einstein", confidence=0.99)
        assert eid is not None
        results = await m.search("E=mc", domain="physics")
        assert len(results) >= 1


class TestConcreteConversationMemory:
    @pytest.mark.asyncio
    async def test_store_and_history(self):
        m = ConcreteConversationMemory(":memory:")
        await m.initialize()
        await m.store("Hello!", session_id="s1", role="user")
        await m.store("Hi there!", session_id="s1", role="assistant")
        await m.store("Another session", session_id="s2")
        history = await m.get_history("s1")
        assert len(history) == 2
        assert history[0]["content"] == "Hello!"
        assert history[1]["content"] == "Hi there!"
