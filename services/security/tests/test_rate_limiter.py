"""Tests for the rate limiter."""

import pytest

from sona_security.infrastructure.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimiter:
    def setup_method(self) -> None:
        config = RateLimitConfig(max_tokens=10, refill_rate=1.0)
        self.limiter = RateLimiter(default_config=config)

    @pytest.mark.asyncio
    async def test_first_request_allowed(self) -> None:
        result = await self.limiter.check_rate_limit("user-1")
        assert result.allowed is True
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_within_limit(self) -> None:
        for _ in range(5):
            result = await self.limiter.check_rate_limit("user-1")
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_exceeds_limit(self) -> None:
        for _ in range(10):
            await self.limiter.check_rate_limit("user-1")
        result = await self.limiter.check_rate_limit("user-1")
        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_per_user_isolation(self) -> None:
        for _ in range(10):
            await self.limiter.check_rate_limit("user-1")
        # user-2 should still have tokens
        result = await self.limiter.check_rate_limit("user-2")
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_per_endpoint_isolation(self) -> None:
        for _ in range(10):
            await self.limiter.check_rate_limit("user-1", "endpoint-a")
        result = await self.limiter.check_rate_limit("user-1", "endpoint-b")
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_endpoint_config(self) -> None:
        self.limiter.configure_endpoint("strict", RateLimitConfig(max_tokens=2, refill_rate=0.1))
        await self.limiter.check_rate_limit("user-1", "strict")
        await self.limiter.check_rate_limit("user-1", "strict")
        result = await self.limiter.check_rate_limit("user-1", "strict")
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_result_has_limit(self) -> None:
        result = await self.limiter.check_rate_limit("user-1")
        assert result.limit == 10

    @pytest.mark.asyncio
    async def test_result_has_reset_at(self) -> None:
        result = await self.limiter.check_rate_limit("user-1")
        assert result.reset_at > 0

    @pytest.mark.asyncio
    async def test_retry_after_on_limit(self) -> None:
        for _ in range(10):
            await self.limiter.check_rate_limit("user-1")
        result = await self.limiter.check_rate_limit("user-1")
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_get_remaining(self) -> None:
        remaining = await self.limiter.get_remaining("user-1")
        assert remaining == 10

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        for _ in range(10):
            await self.limiter.check_rate_limit("user-1")
        await self.limiter.reset("user-1")
        remaining = await self.limiter.get_remaining("user-1")
        assert remaining == 10

    @pytest.mark.asyncio
    async def test_default_config(self) -> None:
        limiter = RateLimiter()
        result = await limiter.check_rate_limit("user-1")
        assert result.allowed is True
        assert result.limit == 100
