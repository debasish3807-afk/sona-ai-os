"""Unit tests for AI Kernel domain errors.

Tests verify error codes, error dataclass construction, and
proper default values.
"""

import pytest

from sona_ai_kernel.domain.errors import ErrorCode, KernelError


class TestErrorCode:
    """Tests for the ErrorCode enum."""

    def test_all_codes_defined(self) -> None:
        """Verify all expected error codes exist."""
        assert ErrorCode.PROVIDER_UNAVAILABLE == "provider_unavailable"
        assert ErrorCode.MODEL_NOT_FOUND == "model_not_found"
        assert ErrorCode.TIMEOUT == "timeout"
        assert ErrorCode.RATE_LIMITED == "rate_limited"
        assert ErrorCode.INVALID_REQUEST == "invalid_request"
        assert ErrorCode.INTERNAL_ERROR == "internal_error"

    def test_error_code_count(self) -> None:
        """Verify exactly 6 error codes exist."""
        assert len(ErrorCode) == 6

    def test_is_str_enum(self) -> None:
        """Error codes are usable as strings."""
        assert str(ErrorCode.TIMEOUT) == "timeout"
        assert str(ErrorCode.PROVIDER_UNAVAILABLE) == "provider_unavailable"


class TestKernelError:
    """Tests for KernelError dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with required fields only."""
        error = KernelError(
            code=ErrorCode.TIMEOUT,
            message="Operation timed out",
        )
        assert error.code == ErrorCode.TIMEOUT
        assert error.message == "Operation timed out"
        assert error.provider is None
        assert error.retryable is False

    def test_with_all_fields(self) -> None:
        """Create with all fields."""
        error = KernelError(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message="Ollama is down",
            provider="ollama",
            retryable=True,
        )
        assert error.code == ErrorCode.PROVIDER_UNAVAILABLE
        assert error.message == "Ollama is down"
        assert error.provider == "ollama"
        assert error.retryable is True

    def test_is_frozen(self) -> None:
        """Verify KernelError is immutable."""
        error = KernelError(code=ErrorCode.TIMEOUT, message="timeout")
        with pytest.raises((TypeError, AttributeError)):
            error.message = "changed"  # type: ignore[misc]

    def test_retryable_errors(self) -> None:
        """Retryable flag is correctly set."""
        retryable = KernelError(
            code=ErrorCode.RATE_LIMITED,
            message="Too many requests",
            retryable=True,
        )
        non_retryable = KernelError(
            code=ErrorCode.INVALID_REQUEST,
            message="Bad input",
            retryable=False,
        )
        assert retryable.retryable is True
        assert non_retryable.retryable is False

    def test_provider_context(self) -> None:
        """Provider field provides error context."""
        error = KernelError(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message="Connection refused",
            provider="openai",
        )
        assert error.provider == "openai"
