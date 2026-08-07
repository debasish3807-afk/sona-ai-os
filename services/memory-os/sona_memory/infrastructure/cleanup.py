"""Memory cleanup service.

Removes expired memories and evicts low-importance entries
when capacity is exceeded. Can run as a background task.
"""

import asyncio

import structlog

from sona_memory.infrastructure.short_term_memory import ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryManager

logger = structlog.get_logger()


class CleanupConfig:
    """Configuration for memory cleanup."""

    def __init__(
        self,
        cleanup_interval_seconds: float = 60.0,
        max_working_memory_age_seconds: float = 1800.0,
        max_short_term_age_seconds: float = 86400.0,
    ) -> None:
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.max_working_memory_age_seconds = max_working_memory_age_seconds
        self.max_short_term_age_seconds = max_short_term_age_seconds


class CleanupService:
    """Handles memory cleanup and expiration.

    Removes expired memories (TTL exceeded) and evicts
    low-importance entries when capacity is exceeded.
    """

    def __init__(
        self,
        working_memory: WorkingMemoryManager,
        short_term: ShortTermMemory,
        config: CleanupConfig | None = None,
    ) -> None:
        self._working = working_memory
        self._short_term = short_term
        self._config = config or CleanupConfig()
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def config(self) -> CleanupConfig:
        """Current cleanup configuration."""
        return self._config

    @property
    def is_running(self) -> bool:
        """Whether the cleanup background task is running."""
        return self._running

    async def cleanup_user(self, user_id: str) -> int:
        """Run cleanup for a specific user.

        Removes expired entries from working and short-term memory.
        Returns total number of entries cleaned up.
        """
        total_cleaned = 0

        # Working memory cleanup
        working_cleaned = await self._working.evict_expired(user_id)
        total_cleaned += working_cleaned

        # Short-term memory cleanup
        st_cleaned = await self._short_term.evict_expired(user_id)
        total_cleaned += st_cleaned

        if total_cleaned > 0:
            logger.info(
                "cleanup_completed",
                user_id=user_id,
                working_cleaned=working_cleaned,
                short_term_cleaned=st_cleaned,
                total=total_cleaned,
            )

        return total_cleaned

    async def cleanup_all_users(self, user_ids: list[str]) -> int:
        """Run cleanup for all provided users."""
        total = 0
        for user_id in user_ids:
            total += await self.cleanup_user(user_id)
        return total

    async def evict_low_importance(self, user_id: str, target_reduction: int = 10) -> int:
        """Evict low-importance entries from short-term memory.

        Removes the least important entries to reduce memory usage.
        """
        entries = await self._short_term.get_all(user_id)
        if not entries:
            return 0

        # Sort by importance ascending (least important first)
        sorted_entries = sorted(entries, key=lambda e: e.importance)

        # Remove the least important ones
        to_remove = sorted_entries[:target_reduction]
        removed = 0
        for entry in to_remove:
            if await self._short_term.remove(user_id, entry.id):
                removed += 1

        if removed > 0:
            logger.info(
                "eviction_completed",
                user_id=user_id,
                evicted=removed,
            )

        return removed

    def start_background_cleanup(self, user_ids_provider: list[str]) -> None:
        """Start periodic background cleanup.

        Args:
            user_ids_provider: List of user IDs to clean up periodically.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._background_loop(user_ids_provider))

    async def stop_background_cleanup(self) -> None:
        """Stop the background cleanup task."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _background_loop(self, user_ids: list[str]) -> None:
        """Background loop for periodic cleanup."""
        while self._running:
            try:
                await self.cleanup_all_users(user_ids)
            except Exception as e:
                logger.error("background_cleanup_error", error=str(e))
            await asyncio.sleep(self._config.cleanup_interval_seconds)
