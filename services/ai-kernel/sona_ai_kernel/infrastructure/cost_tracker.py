"""Cost tracking for LLM inference operations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class CostRecord:
    """Record of a single inference cost event.

    Attributes:
        provider: The provider that served the request.
        model: The model used for inference.
        tokens_input: Number of input tokens consumed.
        tokens_output: Number of output tokens generated.
        cost_input: Cost for input tokens in USD.
        cost_output: Cost for output tokens in USD.
        total_cost: Total cost for this request in USD.
        timestamp: When the request was completed.
        session_id: Associated session identifier.
        user_id: Associated user identifier.
    """

    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_input: float
    cost_output: float
    total_cost: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    session_id: str = ""
    user_id: str = ""


class CostTracker:
    """Tracks inference costs across providers and sessions.

    Maintains a log of all cost records and provides aggregation
    methods for monitoring spending by provider, session, or user.
    """

    def __init__(self) -> None:
        """Initialize an empty cost tracker."""
        self._records: list[CostRecord] = []

    def record(
        self,
        provider: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        cost_per_input: float,
        cost_per_output: float,
        session_id: str = "",
        user_id: str = "",
    ) -> CostRecord:
        """Record a new inference cost event.

        Args:
            provider: The provider name.
            model: The model used.
            tokens_input: Number of input tokens.
            tokens_output: Number of output tokens.
            cost_per_input: Cost per input token in USD.
            cost_per_output: Cost per output token in USD.
            session_id: Optional session identifier.
            user_id: Optional user identifier.

        Returns:
            The created cost record.
        """
        cost_input = tokens_input * cost_per_input
        cost_output = tokens_output * cost_per_output
        total_cost = cost_input + cost_output

        entry = CostRecord(
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_input=cost_input,
            cost_output=cost_output,
            total_cost=total_cost,
            session_id=session_id,
            user_id=user_id,
        )
        self._records.append(entry)
        logger.info(
            "cost_recorded",
            provider=provider,
            model=model,
            total_cost=total_cost,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        )
        return entry

    def get_total_cost(self) -> float:
        """Get the total cost across all records.

        Returns:
            Total cost in USD.
        """
        return sum(r.total_cost for r in self._records)

    def get_session_cost(self, session_id: str) -> float:
        """Get the total cost for a specific session.

        Args:
            session_id: The session to query.

        Returns:
            Total cost for the session in USD.
        """
        return sum(r.total_cost for r in self._records if r.session_id == session_id)

    def get_user_cost(self, user_id: str) -> float:
        """Get the total cost for a specific user.

        Args:
            user_id: The user to query.

        Returns:
            Total cost for the user in USD.
        """
        return sum(r.total_cost for r in self._records if r.user_id == user_id)

    def get_provider_cost(self, provider: str) -> float:
        """Get the total cost for a specific provider.

        Args:
            provider: The provider name to query.

        Returns:
            Total cost for the provider in USD.
        """
        return sum(r.total_cost for r in self._records if r.provider == provider)

    def get_cost_breakdown(self) -> dict[str, float]:
        """Get cost breakdown by provider.

        Returns:
            Dictionary mapping provider names to their total costs.
        """
        breakdown: dict[str, float] = {}
        for record in self._records:
            breakdown[record.provider] = breakdown.get(record.provider, 0.0) + record.total_cost
        return breakdown
