"""Tests for dependency mode configuration."""

import os
from unittest.mock import patch

import pytest

from sona_memory.infrastructure.dependency_mode import (
    DependencyMode,
    DependencyUnavailableError,
    check_dependency_available,
    get_dependency_mode,
    is_strict_mode,
)


class TestDependencyMode:
    """Tests for environment-based dependency mode."""

    def test_default_mode_is_development(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert get_dependency_mode() == DependencyMode.DEVELOPMENT

    def test_production_mode(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "production"}):
            assert get_dependency_mode() == DependencyMode.PRODUCTION
            assert is_strict_mode() is True

    def test_development_mode(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "development"}):
            assert get_dependency_mode() == DependencyMode.DEVELOPMENT
            assert is_strict_mode() is False

    def test_test_mode(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "test"}):
            assert get_dependency_mode() == DependencyMode.TEST
            assert is_strict_mode() is False


class TestCheckDependencyAvailable:
    """Tests for dependency availability checks."""

    def test_connected_no_error(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "production"}):
            # Should not raise when connected
            check_dependency_available("Redis", "redis://localhost:6379", is_connected=True)

    def test_production_unavailable_raises(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "production"}):
            with pytest.raises(DependencyUnavailableError) as exc_info:
                check_dependency_available("Redis", "redis://localhost:6379", is_connected=False)
            assert "Redis" in str(exc_info.value)
            assert "production mode" in str(exc_info.value)

    def test_qdrant_production_unavailable_raises(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "production"}):
            with pytest.raises(DependencyUnavailableError) as exc_info:
                check_dependency_available("Qdrant", "http://localhost:6333", is_connected=False)
            assert "Qdrant" in str(exc_info.value)

    def test_development_fallback_allowed(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "development"}):
            # Should NOT raise — fallback allowed
            check_dependency_available("Redis", "redis://localhost:6379", is_connected=False)

    def test_test_fallback_allowed(self) -> None:
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "test"}):
            # Should NOT raise — fallback allowed
            check_dependency_available("Qdrant", "http://localhost:6333", is_connected=False)

    def test_no_silent_data_loss_in_production(self) -> None:
        """Production mode prevents silent volatile storage."""
        with patch.dict(os.environ, {"SONA_DEPENDENCY_MODE": "production"}):
            with pytest.raises(DependencyUnavailableError):
                check_dependency_available("Redis", "redis://localhost:6379", is_connected=False)
            with pytest.raises(DependencyUnavailableError):
                check_dependency_available("Qdrant", "http://localhost:6333", is_connected=False)
