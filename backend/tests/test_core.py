"""Core module tests — validates fundamental components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExceptions:
    """Test core exception classes."""

    def test_app_exception_base(self):
        """AppException is the base exception."""
        from core.exceptions import AppException

        err = AppException("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)

    def test_validation_error(self):
        """ValidationError for input validation failures."""
        from core.exceptions import ValidationError

        err = ValidationError("invalid input")
        assert isinstance(err, Exception)

    def test_not_found_error(self):
        """NotFoundError for missing resources."""
        from core.exceptions import NotFoundError

        err = NotFoundError("not found")
        assert isinstance(err, Exception)


class TestConstants:
    """Test core constants are defined."""

    def test_header_constants_exist(self):
        """Header constants are defined."""
        from core.constants import HEADER_API_VERSION, HEADER_REQUEST_ID, HEADER_RESPONSE_TIME

        assert HEADER_REQUEST_ID is not None
        assert HEADER_RESPONSE_TIME is not None
        assert HEADER_API_VERSION is not None

    def test_header_constants_are_strings(self):
        """Header constants are strings."""
        from core.constants import HEADER_API_VERSION, HEADER_REQUEST_ID, HEADER_RESPONSE_TIME

        assert isinstance(HEADER_REQUEST_ID, str)
        assert isinstance(HEADER_RESPONSE_TIME, str)
        assert isinstance(HEADER_API_VERSION, str)
