"""Tests for domain errors."""

from dataclasses import FrozenInstanceError

import pytest

from sona_security.domain.errors import SecurityError, SecurityErrorCode


class TestSecurityErrorCode:
    def test_all_codes_defined(self) -> None:
        assert SecurityErrorCode.INVALID_CREDENTIALS == "invalid_credentials"
        assert SecurityErrorCode.TOKEN_EXPIRED == "token_expired"
        assert SecurityErrorCode.TOKEN_REVOKED == "token_revoked"
        assert SecurityErrorCode.PERMISSION_DENIED == "permission_denied"
        assert SecurityErrorCode.RATE_LIMITED == "rate_limited"
        assert SecurityErrorCode.UNSAFE_CONTENT == "unsafe_content"
        assert SecurityErrorCode.PROMPT_INJECTION == "prompt_injection"

    def test_code_count(self) -> None:
        assert len(SecurityErrorCode) == 7

    def test_codes_are_strings(self) -> None:
        for code in SecurityErrorCode:
            assert isinstance(code.value, str)


class TestSecurityError:
    def test_creation(self) -> None:
        error = SecurityError(
            code=SecurityErrorCode.INVALID_CREDENTIALS,
            message="Bad password",
            user_id="user-1",
        )
        assert error.code == SecurityErrorCode.INVALID_CREDENTIALS
        assert error.message == "Bad password"
        assert error.user_id == "user-1"

    def test_default_user_id(self) -> None:
        error = SecurityError(
            code=SecurityErrorCode.TOKEN_EXPIRED,
            message="Token has expired",
        )
        assert error.user_id == ""

    def test_is_frozen(self) -> None:
        error = SecurityError(
            code=SecurityErrorCode.RATE_LIMITED,
            message="Too many requests",
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            error.message = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        e1 = SecurityError(code=SecurityErrorCode.PERMISSION_DENIED, message="denied")
        e2 = SecurityError(code=SecurityErrorCode.PERMISSION_DENIED, message="denied")
        assert e1 == e2

    def test_inequality(self) -> None:
        e1 = SecurityError(code=SecurityErrorCode.PERMISSION_DENIED, message="denied")
        e2 = SecurityError(code=SecurityErrorCode.RATE_LIMITED, message="limited")
        assert e1 != e2
