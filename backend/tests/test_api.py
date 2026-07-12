"""API module tests — validates endpoints and routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHealthEndpoint:
    """Test health check endpoint module."""

    def test_health_module_imports(self):
        """Health module can be imported."""
        from api import health  # noqa: F401

        assert health is not None

    def test_router_module_imports(self):
        """Router module can be imported."""
        from api import router  # noqa: F401

        assert router is not None

    def test_create_api_router(self):
        """create_api_router returns a FastAPI router."""
        from api.router import create_api_router

        api_router = create_api_router()
        assert api_router is not None


class TestVersionEndpoint:
    """Test version endpoint module."""

    def test_version_module_imports(self):
        """Version module can be imported."""
        from api import version  # noqa: F401

        assert version is not None
