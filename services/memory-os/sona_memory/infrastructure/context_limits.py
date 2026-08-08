"""Context limits for Memory OS retrieval.

Ensures AI context construction never grows unbounded.
Preserves highest-relevance memories first.
Handles empty retrieval, duplicates, and oversized entries safely.
"""

from dataclasses import dataclass, field

import structlog

from sona_memory.domain.models import MemoryEntry

logger = structlog.get_logger()

# Default limits (configurable via environment)
DEFAULT_MAX_MEMORIES: int = 20
DEFAULT_MAX_CONTEXT_CHARS: int = 32_000  # ~8K tokens at 4 chars/token
DEFAULT_MAX_SINGLE_MEMORY_CHARS: int = 4_000  # Single memory cap
DEFAULT_TOKEN_BUDGET: int = 8_000  # Approximate token limit


@dataclass(frozen=True)
class ContextLimitsConfig:
    """Configuration for context construction limits."""

    max_memories: int = DEFAULT_MAX_MEMORIES
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS
    max_single_memory_chars: int = DEFAULT_MAX_SINGLE_MEMORY_CHARS
    token_budget: int = DEFAULT_TOKEN_BUDGET


@dataclass
class ContextBuildResult:
    """Result of context construction with limit enforcement."""

    memories: list[MemoryEntry] = field(default_factory=list)
    total_chars: int = 0
    truncated_count: int = 0
    deduplicated_count: int = 0
    oversized_count: int = 0
    original_count: int = 0


def apply_context_limits(
    memories: list[MemoryEntry],
    config: ContextLimitsConfig | None = None,
) -> ContextBuildResult:
    """Apply context limits to a list of retrieved memories.

    Processes memories in order (assumed pre-sorted by relevance).
    Applies:
    1. Deduplication (by memory_id)
    2. Single-memory size cap (truncate oversized)
    3. Total count limit
    4. Total character budget

    Args:
        memories: Pre-sorted memories (highest relevance first).
        config: Limits configuration. Uses defaults if None.

    Returns:
        ContextBuildResult with limited, safe memories.
    """
    if config is None:
        config = ContextLimitsConfig()

    result = ContextBuildResult(original_count=len(memories))

    if not memories:
        return result

    # Deduplicate by memory_id
    seen_ids: set[str] = set()
    unique_memories: list[MemoryEntry] = []
    for mem in memories:
        if mem.id in seen_ids:
            result.deduplicated_count += 1
            continue
        seen_ids.add(mem.id)
        unique_memories.append(mem)

    # Apply limits
    total_chars = 0
    for mem in unique_memories:
        # Count limit
        if len(result.memories) >= config.max_memories:
            result.truncated_count += len(unique_memories) - len(result.memories)
            break

        # Single memory size check
        content_len = len(mem.content)
        if content_len > config.max_single_memory_chars:
            result.oversized_count += 1
            # Truncate oversized memory preserving start
            mem = MemoryEntry(
                id=mem.id,
                content=mem.content[: config.max_single_memory_chars] + "...[truncated]",
                memory_type=mem.memory_type,
                importance=mem.importance,
                created_at=mem.created_at,
                metadata=mem.metadata,
            )
            content_len = len(mem.content)

        # Total budget check
        if total_chars + content_len > config.max_context_chars:
            result.truncated_count += len(unique_memories) - len(result.memories)
            break

        result.memories.append(mem)
        total_chars += content_len

    result.total_chars = total_chars

    if result.truncated_count > 0 or result.deduplicated_count > 0:
        logger.info(
            "context.limits_applied",
            original=result.original_count,
            returned=len(result.memories),
            truncated=result.truncated_count,
            deduplicated=result.deduplicated_count,
            oversized=result.oversized_count,
            total_chars=result.total_chars,
        )

    return result
