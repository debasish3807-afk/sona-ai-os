"""Rate limiting middleware for the API Gateway.

Configurable per-endpoint rate limits with proper 429 responses
and Retry-After headers. Uses token-bucket algorithm (in-memory).
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Rate limit configuration per endpoint category."""

    requests_per_minute: int = 60
    burst_size: int = 10


# Default rate limits by path prefix
DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
    "/v1/chat": RateLimitConfig(requests_per_minute=30, burst_size=5),
    "/v1/models": RateLimitConfig(requests_per_minute=120, burst_size=20),
    "/v1/providers": RateLimitConfig(requests_per_minute=120, burst_size=20),
}

# Endpoints exempt from rate limiting
EXEMPT_PATHS: set[str] = {"/health", "/ready", "/health/detailed", "/docs", "/openapi.json"}


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self) -> bool:
        """Try to consume a token. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    @property
    def retry_after_seconds(self) -> int:
        """Seconds until a token becomes available."""
        if self.tokens >= 1.0:
            return 0
        return max(1, int((1.0 - self.tokens) / self.refill_rate))


def _get_limit_config(path: str) -> RateLimitConfig | None:
    """Get rate limit config for a given path."""
    for prefix, config in DEFAULT_LIMITS.items():
        if path.startswith(prefix):
            return config
    return None


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiting middleware.

    Limits are per client IP + endpoint category.
    Returns 429 with Retry-After header when exceeded.
    """

    def __init__(self, app: object) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._buckets: dict[str, TokenBucket] = defaultdict()

    def _get_client_key(self, request: Request, path: str) -> str:
        """Build a rate limit key from client IP and path prefix."""
        client_ip = request.client.host if request.client else "unknown"
        # Group by path prefix
        for prefix in DEFAULT_LIMITS:
            if path.startswith(prefix):
                return f"{client_ip}:{prefix}"
        return f"{client_ip}:default"

    def _get_or_create_bucket(self, key: str, config: RateLimitConfig) -> TokenBucket:
        """Get existing bucket or create a new one."""
        if key not in self._buckets:
            refill_rate = config.requests_per_minute / 60.0
            self._buckets[key] = TokenBucket(
                capacity=float(config.burst_size),
                tokens=float(config.burst_size),
                refill_rate=refill_rate,
            )
        return self._buckets[key]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Apply rate limiting to non-exempt endpoints."""
        path = request.url.path

        # Exempt health/docs endpoints
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Get rate limit config for this path
        config = _get_limit_config(path)
        if config is None:
            # No specific limit defined — apply default
            config = RateLimitConfig()

        key = self._get_client_key(request, path)
        bucket = self._get_or_create_bucket(key, config)

        if not bucket.consume():
            retry_after = bucket.retry_after_seconds
            logger.warning(
                "rate_limit.exceeded",
                path=path,
                client_key=key,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
