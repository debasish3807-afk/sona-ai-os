"""Application module tests — validates app factory and startup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAppFactory:
    """Test application factory."""

    def test_create_app_returns_fastapi(self):
        """create_app returns a FastAPI instance."""
        from fastapi import FastAPI

        from app.main import create_app

        application = create_app()
        assert isinstance(application, FastAPI)

    def test_create_app_has_routes(self):
        """Created app has registered routes."""
        from app.main import create_app

        application = create_app()
        assert len(application.routes) > 0

    def test_create_app_with_custom_settings(self):
        """create_app accepts custom settings."""
        from app.main import create_app
        from config.settings import Environment, Settings

        settings = Settings(environment=Environment.TESTING, debug=True)
        application = create_app(settings=settings)
        assert application is not None

    def test_app_title_matches_settings(self):
        """App title matches settings.app_name."""
        from app.main import create_app
        from config.settings import Settings

        settings = Settings(app_name="Test App")
        application = create_app(settings=settings)
        assert application.title == "Test App"
