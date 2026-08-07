"""Per-tool circuit breaker for MCP Integration.

Implements the circuit breaker pattern to prevent cascading failures
when individual tools become unreliable.
"""

import time
from enum import StrEnum

import structlog

logger = structlog.get_logger()


class CircuitState(StrEnum):
    """Possible states for a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ToolCircuitBreaker:
    """Circuit breaker for a single tool.

    Tracks consecutive failures and opens the circuit when the
    failure threshold is reached. After a recovery timeout, the
    circuit enters half-open state to allow a trial request.
    """

    def __init__(
        self,
        tool_name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        """Initialize a circuit breaker for a tool.

        Args:
            tool_name: Name of the tool this breaker protects.
            failure_threshold: Consecutive failures before opening.
            recovery_timeout: Seconds before trying half-open.
            success_threshold: Successes in half-open to close.
        """
        self.tool_name = tool_name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._total_failures = 0
        self._total_successes = 0

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state, accounting for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
        return self._state

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._failure_count

    @property
    def total_failures(self) -> int:
        """Total lifetime failures."""
        return self._total_failures

    @property
    def total_successes(self) -> int:
        """Total lifetime successes."""
        return self._total_successes

    def can_execute(self) -> bool:
        """Check if the circuit allows execution.

        Returns:
            True if the circuit is closed or half-open.
        """
        current_state = self.state  # triggers timeout check
        return current_state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Record a successful execution.

        In half-open state, increments the success counter and closes
        the circuit if the threshold is reached.
        """
        self._total_successes += 1
        self._failure_count = 0

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._state = CircuitState.CLOSED
                self._success_count = 0
        else:
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed execution.

        Increments the failure counter and opens the circuit if the
        threshold is reached.
        """
        self._failure_count += 1
        self._total_failures += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open re-opens immediately
            self._state = CircuitState.OPEN
            self._success_count = 0
        elif self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None


class CircuitBreakerRegistry:
    """Manages circuit breakers for all tools.

    Provides per-tool circuit breakers with configurable thresholds.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        """Initialize the circuit breaker registry.

        Args:
            failure_threshold: Default failure threshold for new breakers.
            recovery_timeout: Default recovery timeout for new breakers.
            success_threshold: Default success threshold for new breakers.
        """
        self._breakers: dict[str, ToolCircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold

    def get_breaker(self, tool_name: str) -> ToolCircuitBreaker:
        """Get or create a circuit breaker for a tool.

        Args:
            tool_name: The tool name.

        Returns:
            The ToolCircuitBreaker for the specified tool.
        """
        if tool_name not in self._breakers:
            self._breakers[tool_name] = ToolCircuitBreaker(
                tool_name=tool_name,
                failure_threshold=self._failure_threshold,
                recovery_timeout=self._recovery_timeout,
                success_threshold=self._success_threshold,
            )
        return self._breakers[tool_name]

    def can_execute(self, tool_name: str) -> bool:
        """Check if a tool's circuit allows execution.

        Args:
            tool_name: The tool to check.

        Returns:
            True if the circuit is not open.
        """
        return self.get_breaker(tool_name).can_execute()

    def record_success(self, tool_name: str) -> None:
        """Record a successful tool execution.

        Args:
            tool_name: The tool that succeeded.
        """
        self.get_breaker(tool_name).record_success()

    def record_failure(self, tool_name: str) -> None:
        """Record a failed tool execution.

        Args:
            tool_name: The tool that failed.
        """
        self.get_breaker(tool_name).record_failure()

    def get_state(self, tool_name: str) -> CircuitState:
        """Get the circuit state for a tool.

        Args:
            tool_name: The tool to check.

        Returns:
            The current CircuitState.
        """
        return self.get_breaker(tool_name).state

    def reset(self, tool_name: str) -> None:
        """Reset a tool's circuit breaker.

        Args:
            tool_name: The tool to reset.
        """
        if tool_name in self._breakers:
            self._breakers[tool_name].reset()

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()

    @property
    def breaker_count(self) -> int:
        """Return the number of tracked circuit breakers."""
        return len(self._breakers)
