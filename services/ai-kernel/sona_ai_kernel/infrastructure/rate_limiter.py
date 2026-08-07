"""Token bucket rate limiter for provider request throttling."""

import asyncio
import time
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_second: Refill rate for the token bucket.
        burst_size: Maximum tokens the bucket can hold.
        per_provider: Whether to create separate limiters per provider.
    """

    requests_per_second: float = 10.0
    burst_size: int = 20
    per_provider: bool = True


class TokenBucketRateLimiter:
    """Token bucket algorithm for rate limiting.

    Allows bursts up to the bucket capacity, then throttles
    to the configured rate.
    """

    def __init__(self, rate: float, burst: int) -> None:
        """Initialize token bucket rate limiter.

        Args:
            rate: Tokens added per second.
            burst: Maximum bucket capacity.
        """
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.time()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self, timeout: float = 30.0) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait for a token in seconds.

        Returns:
            True if a token was acquired, False on timeout.
        """
        deadline = time.time() + timeout

        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

            # Calculate wait time for next token
            async with self._lock:
                wait_time = (1.0 - self._tokens) / self._rate if self._rate > 0 else timeout

            if time.time() + wait_time > deadline:
                return False

            await asyncio.sleep(min(wait_time, 0.1))

    @property
    def available_tokens(self) -> float:
        """Return the current number of available tokens.

        Returns:
            The number of tokens currently in the bucket.
        """
        self._refill()
        return self._tokens


class RateLimiterRegistry:
    """Manages per-provider rate limiters.

    Creates and caches rate limiters for each provider, with
    configurable defaults and per-provider overrides.
    """

    def __init__(self, default_config: RateLimitConfig | None = None) -> None:
        """Initialize rate limiter registry.

        Args:
            default_config: Default configuration for new limiters.
        """
        self._config = default_config or RateLimitConfig()
        self._limiters: dict[str, TokenBucketRateLimiter] = {}

    def get_limiter(self, provider: str) -> TokenBucketRateLimiter:
        """Get or create a rate limiter for a provider.

        Args:
            provider: The provider name.

        Returns:
            The rate limiter for the specified provider.
        """
        if provider not in self._limiters:
            self._limiters[provider] = TokenBucketRateLimiter(
                rate=self._config.requests_per_second,
                burst=self._config.burst_size,
            )
            logger.info(
                "rate_limiter_created",
                provider=provider,
                rate=self._config.requests_per_second,
                burst=self._config.burst_size,
            )
        return self._limiters[provider]

    def configure(self, provider: str, rate: float, burst: int) -> None:
        """Configure a specific provider's rate limiter.

        Creates a new limiter with the specified parameters, replacing
        any existing one for this provider.

        Args:
            provider: The provider name.
            rate: Tokens per second.
            burst: Maximum bucket capacity.
        """
        self._limiters[provider] = TokenBucketRateLimiter(rate=rate, burst=burst)
        logger.info(
            "rate_limiter_configured",
            provider=provider,
            rate=rate,
            burst=burst,
        )
