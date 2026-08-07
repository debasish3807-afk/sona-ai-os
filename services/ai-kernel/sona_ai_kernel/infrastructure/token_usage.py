"""Token usage tracking and budget management.

Tracks token consumption across requests for observability,
cost analysis, and potential budget enforcement.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageRecord:
    """Record of token usage from a single LLM call.

    Attributes:
        provider: The provider that served the request.
        model: The model used for generation.
        tokens_input: Number of input/prompt tokens consumed.
        tokens_output: Number of output/completion tokens generated.
        latency_ms: Total request latency in milliseconds.
        session_id: The session this usage belongs to.
    """

    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    session_id: str


class TokenUsageManager:
    """Tracks token consumption across requests.

    Maintains an in-memory log of all usage records and provides
    aggregation methods for session-level and global reporting.
    """

    def __init__(self) -> None:
        """Initialize an empty usage manager."""
        self._records: list[UsageRecord] = []

    def record(self, usage: UsageRecord) -> None:
        """Record a token usage event.

        Args:
            usage: The usage record to store.
        """
        self._records.append(usage)

    def get_session_usage(self, session_id: str) -> dict[str, int]:
        """Get aggregated token usage for a specific session.

        Args:
            session_id: The session to query.

        Returns:
            Dictionary with 'tokens_input', 'tokens_output', and 'total' keys.
        """
        tokens_input = 0
        tokens_output = 0
        for record in self._records:
            if record.session_id == session_id:
                tokens_input += record.tokens_input
                tokens_output += record.tokens_output
        return {
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "total": tokens_input + tokens_output,
        }

    def get_total_usage(self) -> dict[str, int]:
        """Get aggregated token usage across all sessions.

        Returns:
            Dictionary with 'tokens_input', 'tokens_output', 'total',
            and 'request_count' keys.
        """
        tokens_input = sum(r.tokens_input for r in self._records)
        tokens_output = sum(r.tokens_output for r in self._records)
        return {
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "total": tokens_input + tokens_output,
            "request_count": len(self._records),
        }

    def get_provider_usage(self, provider: str) -> dict[str, int]:
        """Get aggregated token usage for a specific provider.

        Args:
            provider: The provider name to query.

        Returns:
            Dictionary with 'tokens_input', 'tokens_output', and 'total' keys.
        """
        tokens_input = 0
        tokens_output = 0
        for record in self._records:
            if record.provider == provider:
                tokens_input += record.tokens_input
                tokens_output += record.tokens_output
        return {
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "total": tokens_input + tokens_output,
        }

    def clear(self) -> None:
        """Clear all usage records."""
        self._records.clear()
