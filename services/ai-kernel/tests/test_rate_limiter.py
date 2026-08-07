"""Unit tests for the rate limiter module.

Tests verify token bucket algorithm, acquire/refill, timeout, and registry.
"""

import asyncio

import pytest

from sona_ai_kernel.infrastructure.rate_limiter import (
    RateLimitConfig,
    RateLimiterRegistry,
    TokenBucketRateLimiter,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_values(self) -> None:
        """Verify default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_second == 10.0
        assert config.burst_size == 20
        assert config.per_provider is True


class TestTokenBucketRateLimiter:
    """Tests for the TokenBucketRateLimiter."""

    @pytest.mark.asyncio
    async def test_acquire_succeeds_with_available_tokens(self) -> None:
        """Acquire succeeds immediately when tokens are available."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        assert await limiter.acquire(timeout=1.0) is True

    @pytest.mark.asyncio
    async def test_burst_allows_rapid_acquisition(self) -> None:
        """Multiple rapid acquires work up to burst capacity."""
        limiter = TokenBucketRateLimiter(rate=1.0, burst=3)

        # Should be able to acquire 3 immediately
        assert await limiter.acquire(timeout=0.1) is True
        assert await limiter.acquire(timeout=0.1) is True
        assert await limiter.acquire(timeout=0.1) is True

    @pytest.mark.asyncio
    async def test_acquire_times_out_when_empty(self) -> None:
        """Acquire returns False when tokens exhausted and timeout expires."""
        limiter = TokenBucketRateLimiter(rate=0.5, burst=1)

        # Exhaust the single token
        assert await limiter.acquire(timeout=0.1) is True
        # Should timeout waiting for next token
        assert await limiter.acquire(timeout=0.1) is False

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self) -> None:
        """Tokens refill based on rate after time passes."""
        limiter = TokenBucketRateLimiter(rate=100.0, burst=5)

        # Exhaust all tokens
        for _ in range(5):
            await limiter.acquire(timeout=0.1)

        # Wait for refill
        await asyncio.sleep(0.05)

        # Should have some tokens now
        assert limiter.available_tokens > 0

    def test_available_tokens_property(self) -> None:
        """available_tokens reflects current bucket level."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=10)
        assert limiter.available_tokens == 10.0

    @pytest.mark.asyncio
    async def test_tokens_capped_at_burst(self) -> None:
        """Tokens never exceed burst capacity."""
        limiter = TokenBucketRateLimiter(rate=1000.0, burst=5)

        # Wait some time for lots of refill
        await asyncio.sleep(0.01)

        assert limiter.available_tokens <= 5.0


class TestRateLimiterRegistry:
    """Tests for the RateLimiterRegistry."""

    def test_creates_limiter_on_first_access(self) -> None:
        """Creates a new limiter when first accessed for a provider."""
        registry = RateLimiterRegistry()
        limiter = registry.get_limiter("openai")
        assert isinstance(limiter, TokenBucketRateLimiter)

    def test_returns_same_limiter_on_subsequent_access(self) -> None:
        """Returns the same limiter instance for the same provider."""
        registry = RateLimiterRegistry()
        limiter1 = registry.get_limiter("openai")
        limiter2 = registry.get_limiter("openai")
        assert limiter1 is limiter2

    def test_different_providers_get_different_limiters(self) -> None:
        """Different providers get separate limiter instances."""
        registry = RateLimiterRegistry()
        limiter1 = registry.get_limiter("openai")
        limiter2 = registry.get_limiter("anthropic")
        assert limiter1 is not limiter2

    def test_configure_replaces_limiter(self) -> None:
        """configure() creates a new limiter with custom settings."""
        registry = RateLimiterRegistry()
        original = registry.get_limiter("openai")
        registry.configure("openai", rate=5.0, burst=10)
        new = registry.get_limiter("openai")
        assert original is not new

    def test_custom_default_config(self) -> None:
        """Registry uses custom default config for new limiters."""
        config = RateLimitConfig(requests_per_second=5.0, burst_size=10)
        registry = RateLimiterRegistry(default_config=config)
        limiter = registry.get_limiter("test")
        assert limiter.available_tokens == 10.0
