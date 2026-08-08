"""Tests for Memory OS context limits."""

from datetime import UTC, datetime

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.context_limits import (
    ContextLimitsConfig,
    apply_context_limits,
)


def _make_memory(mid: str, content: str, importance: float = 0.5) -> MemoryEntry:
    return MemoryEntry(
        id=mid,
        memory_type=MemoryType.EPISODIC,
        content=content,
        importance=importance,
        created_at=datetime.now(UTC),
    )


class TestContextLimits:
    def test_empty_retrieval(self) -> None:
        result = apply_context_limits([])
        assert result.memories == []
        assert result.total_chars == 0

    def test_normal_context(self) -> None:
        memories = [_make_memory(f"m{i}", f"Memory {i}") for i in range(5)]
        result = apply_context_limits(memories)
        assert len(result.memories) == 5
        assert result.truncated_count == 0

    def test_max_memories_limit(self) -> None:
        config = ContextLimitsConfig(max_memories=3)
        memories = [_make_memory(f"m{i}", f"Memory {i}") for i in range(10)]
        result = apply_context_limits(memories, config)
        assert len(result.memories) == 3
        assert result.truncated_count == 7

    def test_max_context_chars_limit(self) -> None:
        config = ContextLimitsConfig(max_context_chars=50, max_memories=100)
        memories = [_make_memory(f"m{i}", "A" * 20) for i in range(10)]
        result = apply_context_limits(memories, config)
        assert result.total_chars <= 50
        assert len(result.memories) <= 3

    def test_oversized_single_memory_truncated(self) -> None:
        config = ContextLimitsConfig(max_single_memory_chars=100)
        big = _make_memory("big", "X" * 500)
        result = apply_context_limits([big], config)
        assert len(result.memories) == 1
        assert len(result.memories[0].content) < 500
        assert result.memories[0].content.endswith("...[truncated]")
        assert result.oversized_count == 1

    def test_deduplication(self) -> None:
        memories = [
            _make_memory("dup", "Same content"),
            _make_memory("dup", "Same content"),
            _make_memory("unique", "Different"),
        ]
        result = apply_context_limits(memories)
        assert len(result.memories) == 2
        assert result.deduplicated_count == 1

    def test_preserves_relevance_order(self) -> None:
        config = ContextLimitsConfig(max_memories=2)
        memories = [
            _make_memory("high", "Important", importance=0.9),
            _make_memory("med", "Medium", importance=0.5),
            _make_memory("low", "Low", importance=0.1),
        ]
        result = apply_context_limits(memories, config)
        assert result.memories[0].id == "high"
        assert result.memories[1].id == "med"

    def test_default_config_values(self) -> None:
        config = ContextLimitsConfig()
        assert config.max_memories == 20
        assert config.max_context_chars == 32_000
        assert config.max_single_memory_chars == 4_000
        assert config.token_budget == 8_000
