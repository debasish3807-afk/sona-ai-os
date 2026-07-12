"""Configuration module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSettings:
    """Test settings configuration."""

    def test_settings_instantiation(self):
        """Settings can be instantiated with defaults."""
        from config.settings import Settings

        settings = Settings()
        assert settings is not None

    def test_settings_app_name(self):
        """Settings has app_name."""
        from config.settings import Settings

        settings = Settings()
        assert settings.app_name is not None
        assert isinstance(settings.app_name, str)
        assert len(settings.app_name) > 0

    def test_settings_app_version(self):
        """Settings has a version string."""
        from config.settings import Settings

        settings = Settings()
        assert settings.app_version is not None

    def test_settings_is_production_default(self):
        """Default environment is not production."""
        from config.settings import Settings

        settings = Settings()
        assert settings.is_production is False

    def test_settings_production_detection(self):
        """Production environment is detected correctly."""
        from config.settings import Environment, Settings

        settings = Settings(environment=Environment.PRODUCTION)
        assert settings.is_production is True

    def test_get_settings_singleton(self):
        """get_settings returns a cached instance."""
        from config.settings import get_settings

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
