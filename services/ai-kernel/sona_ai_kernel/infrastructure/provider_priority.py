"""Provider priority and failover management."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class ProviderPriority:
    """Priority configuration for a single provider.

    Attributes:
        provider_name: Unique name identifying the provider.
        priority: Lower number means higher priority (0 is highest).
        weight: Weight for weighted selection among same-priority providers.
        is_fallback: If True, only used when primary providers fail.
    """

    provider_name: str
    priority: int = 0
    weight: float = 1.0
    is_fallback: bool = False


class ProviderPriorityManager:
    """Manages provider selection order with failover.

    Maintains an ordered list of providers and supports querying
    for the next available provider when previous ones fail.
    """

    def __init__(self) -> None:
        """Initialize an empty priority manager."""
        self._priorities: list[ProviderPriority] = []

    def add(self, priority: ProviderPriority) -> None:
        """Add a provider priority entry.

        Args:
            priority: The provider priority configuration to add.
        """
        self._priorities.append(priority)
        self._priorities.sort(key=lambda p: (p.is_fallback, p.priority, -p.weight))
        logger.info(
            "provider_priority_added",
            provider=priority.provider_name,
            priority=priority.priority,
            is_fallback=priority.is_fallback,
        )

    def get_ordered(self, exclude: set[str] | None = None) -> list[str]:
        """Get provider names in priority order, excluding specified ones.

        Args:
            exclude: Set of provider names to exclude from the result.

        Returns:
            List of provider names sorted by priority.
        """
        excluded = exclude or set()
        return [p.provider_name for p in self._priorities if p.provider_name not in excluded]

    def get_fallbacks(self) -> list[str]:
        """Get all fallback provider names in priority order.

        Returns:
            List of fallback provider names.
        """
        return [p.provider_name for p in self._priorities if p.is_fallback]

    def get_next(self, failed: set[str]) -> str | None:
        """Get the next available provider after failures.

        Args:
            failed: Set of provider names that have already failed.

        Returns:
            The next provider name to try, or None if all exhausted.
        """
        for p in self._priorities:
            if p.provider_name not in failed:
                return p.provider_name
        return None
