"""Circuit breaker for provider fault tolerance.

States: CLOSED (normal) → OPEN (blocking) → HALF_OPEN (testing)
"""

import time
from dataclasses import dataclass
from enum import StrEnum

import structlog

logger = structlog.get_logger()


class CircuitState(StrEnum):
    """Possible states of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Number of failures before opening the circuit.
        recovery_timeout: Seconds before transitioning from OPEN to HALF_OPEN.
        success_threshold: Successes in HALF_OPEN needed to close the circuit.
        half_open_max_calls: Maximum concurrent calls allowed in HALF_OPEN state.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2
    half_open_max_calls: int = 1


class CircuitBreaker:
    """Per-provider circuit breaker preventing cascade failures.

    Tracks failures for a named provider and transitions between CLOSED,
    OPEN, and HALF_OPEN states to protect the system from repeated failures.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        """Initialize circuit breaker for a provider.

        Args:
            name: The provider name this breaker protects.
            config: Circuit breaker configuration. Uses defaults if None.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Return the current circuit state, transitioning OPEN→HALF_OPEN if timeout elapsed."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._success_count = 0
        return self._state

    def can_execute(self) -> bool:
        """Check whether a request is allowed to proceed.

        Returns:
            True if the circuit allows execution, False otherwise.
        """
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls
        return False  # OPEN

    def record_success(self) -> None:
        """Record a successful request execution.

        In HALF_OPEN state, counts successes toward closing the circuit.
        In CLOSED state, resets the failure counter.
        """
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("circuit_closed", provider=self.name)
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed request execution.

        Increments the failure counter. In HALF_OPEN state, immediately
        reopens the circuit. In CLOSED state, opens the circuit when the
        failure threshold is reached.
        """
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("circuit_reopened", provider=self.name)
        elif self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning("circuit_opened", provider=self.name, failures=self._failure_count)

    def reset(self) -> None:
        """Reset the circuit breaker to its initial CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
