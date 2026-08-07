"""Token bucket rate limiter.

Implements per-user rate limiting with configurable rates per endpoint.
"""

import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_tokens: int = 100
    refill_rate: float = 10.0  # tokens per second
    refill_interval: float = 1.0  # seconds


@dataclass
class TokenBucket:
    """Token bucket state for a single user/endpoint."""

    tokens: float
    max_tokens: int
    refill_rate: float
    last_refill: float = field(default_factory=time.time)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    limit: int
    reset_at: float
    retry_after: float = 0.0


class RateLimiter:
    """Per-user token bucket rate limiter."""

    def __init__(self, default_config: RateLimitConfig | None = None) -> None:
        self._default_config = default_config or RateLimitConfig()
        self._endpoint_configs: dict[str, RateLimitConfig] = {}
        self._buckets: dict[str, TokenBucket] = {}  # key: "user_id:endpoint"

    def configure_endpoint(self, endpoint: str, config: RateLimitConfig) -> None:
        """Set rate limit configuration for a specific endpoint."""
        self._endpoint_configs[endpoint] = config

    async def check_rate_limit(self, user_id: str, endpoint: str = "default") -> RateLimitResult:
        """Check if a request is within rate limits.

        Returns:
            RateLimitResult with allowed status and metadata.
        """
        bucket_key = f"{user_id}:{endpoint}"
        config = self._endpoint_configs.get(endpoint, self._default_config)
        bucket = self._get_or_create_bucket(bucket_key, config)

        # Refill tokens
        now = time.time()
        elapsed = now - bucket.last_refill
        tokens_to_add = elapsed * bucket.refill_rate
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + tokens_to_add)
        bucket.last_refill = now

        # Consume token
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            remaining = int(bucket.tokens)
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                limit=bucket.max_tokens,
                reset_at=now + (bucket.max_tokens - bucket.tokens) / bucket.refill_rate,
            )

        # Rate limited
        retry_after = (1.0 - bucket.tokens) / bucket.refill_rate
        logger.warning(
            "rate_limit_exceeded",
            user_id=user_id,
            endpoint=endpoint,
            retry_after=retry_after,
        )
        return RateLimitResult(
            allowed=False,
            remaining=0,
            limit=bucket.max_tokens,
            reset_at=now + retry_after,
            retry_after=retry_after,
        )

    async def get_remaining(self, user_id: str, endpoint: str = "default") -> int:
        """Get remaining tokens for a user/endpoint."""
        bucket_key = f"{user_id}:{endpoint}"
        config = self._endpoint_configs.get(endpoint, self._default_config)
        bucket = self._get_or_create_bucket(bucket_key, config)

        # Refill tokens
        now = time.time()
        elapsed = now - bucket.last_refill
        tokens_to_add = elapsed * bucket.refill_rate
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + tokens_to_add)
        bucket.last_refill = now

        return int(bucket.tokens)

    async def reset(self, user_id: str, endpoint: str = "default") -> None:
        """Reset rate limit for a user/endpoint."""
        bucket_key = f"{user_id}:{endpoint}"
        if bucket_key in self._buckets:
            config = self._endpoint_configs.get(endpoint, self._default_config)
            self._buckets[bucket_key] = TokenBucket(
                tokens=float(config.max_tokens),
                max_tokens=config.max_tokens,
                refill_rate=config.refill_rate,
            )

    def _get_or_create_bucket(self, bucket_key: str, config: RateLimitConfig) -> TokenBucket:
        """Get or create a token bucket for the given key."""
        if bucket_key not in self._buckets:
            self._buckets[bucket_key] = TokenBucket(
                tokens=float(config.max_tokens),
                max_tokens=config.max_tokens,
                refill_rate=config.refill_rate,
            )
        return self._buckets[bucket_key]
