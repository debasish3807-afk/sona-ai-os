"""Episodic memory - specific events and experiences.

This module defines the episodic memory interface which manages discrete
events and experiences with rich temporal context. Episodic memory captures
the "what happened, when, and with whom" aspects of interactions.

Unlike semantic memory (which stores facts), episodic memory preserves
the narrative structure and temporal relationships between events,
enabling timeline reconstruction and experiential recall.

Classes:
    EpisodicConfig: Configuration for episodic memory behavior.
    Episode: A discrete event or experience with temporal context.
    EpisodicMemory: Abstract interface extending MemoryStore for episodic memory.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .base import MemoryStore


@dataclass(frozen=True, slots=True)
class EpisodicConfig:
    """Configuration for episodic memory behavior.

    Controls capacity, detail preservation, and episode linking behavior.

    Attributes:
        max_episodes: Maximum number of episodes to retain.
        detail_level: Level of detail to preserve in episodes ('full', 'standard', 'minimal').
        link_related: Whether to automatically link related episodes.
        max_entries_per_episode: Maximum memory entries per single episode.
        auto_detect_episodes: Whether to auto-detect episode boundaries.
    """

    max_episodes: int = 10000
    detail_level: str = "standard"
    link_related: bool = True
    max_entries_per_episode: int = 100
    auto_detect_episodes: bool = True


@dataclass(slots=True)
class Episode:
    """A discrete event or experience with temporal context.

    An Episode groups related memory entries into a coherent narrative
    unit with explicit start/end times, participants, and outcome.

    Attributes:
        episode_id: Unique identifier for this episode (UUID4).
        title: Brief descriptive title for the episode.
        description: Longer description of what occurred.
        entries: List of memory entry IDs that comprise this episode.
        start_time: UTC timestamp when the episode began.
        end_time: Optional UTC timestamp when the episode ended.
        participants: List of participant identifiers (user IDs, agent IDs).
        outcome: Optional description of the episode's outcome/result.
        linked_episodes: IDs of related episodes.
        metadata: Additional episode metadata.
    """

    title: str
    description: str
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entries: list[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    participants: list[str] = field(default_factory=list)
    outcome: str | None = None
    linked_episodes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class EpisodicMemory(MemoryStore):
    """Abstract interface for episodic memory operations.

    Extends the base MemoryStore with episode-specific operations
    including episode storage, timeline queries, and episode linking.
    """

    @abstractmethod
    async def store_episode(self, episode: Episode) -> str:
        """Store a new episode.

        Persists the episode with all its metadata and entry references.

        Args:
            episode: The episode to store.

        Returns:
            The episode_id of the stored episode.
        """
        ...

    @abstractmethod
    async def get_episode(self, episode_id: str) -> Episode | None:
        """Retrieve a single episode by its ID.

        Args:
            episode_id: The unique identifier of the episode.

        Returns:
            The episode if found, None otherwise.
        """
        ...

    @abstractmethod
    async def search_episodes(
        self,
        query: str,
        time_range: tuple[datetime, datetime] | None = None,
        max_results: int = 20,
    ) -> list[Episode]:
        """Search for episodes matching a query within an optional time range.

        Args:
            query: Search query text.
            time_range: Optional (start, end) tuple for temporal filtering.
            max_results: Maximum number of episodes to return.

        Returns:
            List of matching episodes ordered by relevance.
        """
        ...

    @abstractmethod
    async def get_timeline(self, start: datetime, end: datetime) -> list[Episode]:
        """Get all episodes within a time range as a chronological timeline.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List of episodes ordered chronologically within the range.
        """
        ...

    @abstractmethod
    async def link_episodes(self, episode_ids: list[str]) -> None:
        """Link multiple episodes as related to each other.

        Creates bidirectional relationships between the specified episodes.

        Args:
            episode_ids: List of episode IDs to link together.
        """
        ...
