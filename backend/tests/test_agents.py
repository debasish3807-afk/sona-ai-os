"""Agent module tests — validates multi-agent framework."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentImports:
    """Test that agent modules can be imported."""

    def test_agents_package_imports(self):
        """Agents package imports successfully."""
        import agents  # noqa: F401

        assert agents is not None

    def test_agent_base_imports(self):
        """Base agent module imports."""
        from agents import base  # noqa: F401

        assert base is not None

    def test_agent_coordinator_imports(self):
        """Agent coordinator imports."""
        from agents import coordinator  # noqa: F401

        assert coordinator is not None

    def test_agent_manager_imports(self):
        """Agent manager imports."""
        from agents import manager  # noqa: F401

        assert manager is not None

    def test_agent_registry_imports(self):
        """Agent registry imports."""
        from agents import registry  # noqa: F401

        assert registry is not None

    def test_agent_factory_imports(self):
        """Agent factory imports."""
        from agents import factory  # noqa: F401

        assert factory is not None
