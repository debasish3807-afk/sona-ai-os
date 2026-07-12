"""Memory module tests — validates memory engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMemoryImports:
    """Test that memory modules can be imported."""

    def test_memory_package_imports(self):
        """Memory package imports successfully."""
        import memory  # noqa: F401

        assert memory is not None

    def test_memory_base_imports(self):
        """Base memory module imports."""
        from memory import base  # noqa: F401

        assert base is not None

    def test_memory_manager_imports(self):
        """Memory manager imports."""
        from memory import manager  # noqa: F401

        assert manager is not None

    def test_memory_working_imports(self):
        """Working memory imports."""
        from memory import working  # noqa: F401

        assert working is not None

    def test_memory_long_term_imports(self):
        """Long-term memory imports."""
        from memory import long_term  # noqa: F401

        assert long_term is not None

    def test_memory_semantic_imports(self):
        """Semantic memory imports."""
        from memory import semantic  # noqa: F401

        assert semantic is not None

    def test_memory_types_imports(self):
        """Memory types imports."""
        from memory import types  # noqa: F401

        assert types is not None
