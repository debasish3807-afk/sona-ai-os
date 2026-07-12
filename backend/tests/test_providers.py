"""Provider module tests — validates AI provider architecture."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProviderImports:
    """Test that provider modules can be imported."""

    def test_providers_package_imports(self):
        """Providers package imports successfully."""
        import providers  # noqa: F401

        assert providers is not None

    def test_provider_base_imports(self):
        """Base provider module imports."""
        from providers import base  # noqa: F401

        assert base is not None

    def test_provider_registry_imports(self):
        """Provider registry imports."""
        from providers import registry  # noqa: F401

        assert registry is not None

    def test_provider_manager_imports(self):
        """Provider manager imports."""
        from providers import manager  # noqa: F401

        assert manager is not None

    def test_provider_factory_imports(self):
        """Provider factory imports."""
        from providers import factory  # noqa: F401

        assert factory is not None

    def test_provider_types_imports(self):
        """Provider types imports."""
        from providers import types  # noqa: F401

        assert types is not None
