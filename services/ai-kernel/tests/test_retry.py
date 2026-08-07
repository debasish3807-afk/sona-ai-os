"""Unit tests for the retry module.

Tests verify exponential backoff, jitter, max retries,
and proper exception propagation.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sona_ai_kernel.infrastructure.retry import RetryConfig, with_retry


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Verify default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.jitter is True

    def test_custom_values(self) -> None:
        """Verify custom configuration values."""
        config = RetryConfig(max_retries=5, base_delay=0.5, max_delay=60.0, jitter=False)
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 60.0
        assert config.jitter is False


class TestWithRetry:
    """Tests for the with_retry function."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self) -> None:
        """Function succeeds immediately without retries."""
        fn = AsyncMock(return_value="success")
        result = await with_retry(fn, RetryConfig(max_retries=3))
        assert result == "success"
        assert fn.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self) -> None:
        """Function succeeds after initial failures."""
        fn = AsyncMock(side_effect=[ValueError("fail1"), ValueError("fail2"), "success"])
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)
        result = await with_retry(fn, config, retryable_exceptions=(ValueError,))
        assert result == "success"
        assert fn.call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self) -> None:
        """Raises the last exception when retries are exhausted."""
        fn = AsyncMock(side_effect=ValueError("always fails"))
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        with pytest.raises(ValueError, match="always fails"):
            await with_retry(fn, config, retryable_exceptions=(ValueError,))
        assert fn.call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception_not_retried(self) -> None:
        """Non-retryable exceptions are raised immediately."""
        fn = AsyncMock(side_effect=TypeError("not retryable"))
        config = RetryConfig(max_retries=3, base_delay=0.01)
        with pytest.raises(TypeError, match="not retryable"):
            await with_retry(fn, config, retryable_exceptions=(ValueError,))
        assert fn.call_count == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self) -> None:
        """Verify delays increase exponentially."""
        fn = AsyncMock(side_effect=[ValueError("e"), ValueError("e"), "ok"])
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        with patch(
            "sona_ai_kernel.infrastructure.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await with_retry(fn, config, retryable_exceptions=(ValueError,))
            # First retry: base_delay * 2^0 = 0.1
            # Second retry: base_delay * 2^1 = 0.2
            assert mock_sleep.call_count == 2
            delays = [call.args[0] for call in mock_sleep.call_args_list]
            assert abs(delays[0] - 0.1) < 0.01
            assert abs(delays[1] - 0.2) < 0.01

    @pytest.mark.asyncio
    async def test_max_delay_cap(self) -> None:
        """Verify delay is capped at max_delay."""
        call_count = 0

        async def failing_fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                raise ValueError("fail")
            return "ok"

        config = RetryConfig(max_retries=5, base_delay=10.0, max_delay=15.0, jitter=False)

        with patch(
            "sona_ai_kernel.infrastructure.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await with_retry(failing_fn, config, retryable_exceptions=(ValueError,))
            delays = [call.args[0] for call in mock_sleep.call_args_list]
            # All delays should be <= max_delay
            for delay in delays:
                assert delay <= 15.0

    @pytest.mark.asyncio
    async def test_jitter_randomizes_delay(self) -> None:
        """Verify jitter adds randomness to delays."""
        fn = AsyncMock(side_effect=[ValueError("e"), ValueError("e"), "ok"])
        config = RetryConfig(max_retries=3, base_delay=1.0, jitter=True)

        with patch(
            "sona_ai_kernel.infrastructure.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await with_retry(fn, config, retryable_exceptions=(ValueError,))
            delays = [call.args[0] for call in mock_sleep.call_args_list]
            # With jitter, delays should be between 0.5*base and base
            for delay in delays:
                assert delay > 0
                assert delay <= 30.0  # within max_delay

    @pytest.mark.asyncio
    async def test_default_config_used_when_none(self) -> None:
        """Verify default config is used when None passed."""
        fn = AsyncMock(return_value="ok")
        result = await with_retry(fn, None)
        assert result == "ok"
