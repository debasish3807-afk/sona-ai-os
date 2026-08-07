"""Unit tests for the timeout module.

Tests verify timeout wrapping, successful execution within time limits,
and proper TimeoutError raising.
"""

import asyncio

import pytest
from sona_ai_kernel.infrastructure.timeout import with_timeout


class TestWithTimeout:
    """Tests for the with_timeout function."""

    @pytest.mark.asyncio
    async def test_success_within_timeout(self) -> None:
        """Operation completing within timeout returns result."""

        async def fast_op() -> str:
            return "done"

        result = await with_timeout(fast_op(), timeout_seconds=5.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_raises_timeout_error(self) -> None:
        """Operation exceeding timeout raises TimeoutError."""

        async def slow_op() -> str:
            await asyncio.sleep(10.0)
            return "never"

        with pytest.raises(TimeoutError, match="timed out after 0.05s"):
            await with_timeout(slow_op(), timeout_seconds=0.05)

    @pytest.mark.asyncio
    async def test_timeout_error_message_contains_seconds(self) -> None:
        """Error message includes the timeout value."""

        async def slow_op() -> str:
            await asyncio.sleep(10.0)
            return "never"

        with pytest.raises(TimeoutError) as exc_info:
            await with_timeout(slow_op(), timeout_seconds=0.01)
        assert "0.01" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_preserves_return_type(self) -> None:
        """Return value type is preserved through the wrapper."""

        async def returns_int() -> int:
            return 42

        result = await with_timeout(returns_int(), timeout_seconds=5.0)
        assert result == 42
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_exception_propagated_not_timeout(self) -> None:
        """Non-timeout exceptions are propagated normally."""

        async def raises_value_error() -> str:
            raise ValueError("custom error")

        with pytest.raises(ValueError, match="custom error"):
            await with_timeout(raises_value_error(), timeout_seconds=5.0)

    @pytest.mark.asyncio
    async def test_near_boundary_succeeds(self) -> None:
        """Operation that finishes just before timeout succeeds."""

        async def near_boundary() -> str:
            await asyncio.sleep(0.01)
            return "made it"

        result = await with_timeout(near_boundary(), timeout_seconds=1.0)
        assert result == "made it"
