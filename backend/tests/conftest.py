"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app_settings():
    """Provide test settings."""
    from config.settings import Environment, Settings

    return Settings(
        environment=Environment.TESTING,
        debug=True,
    )
