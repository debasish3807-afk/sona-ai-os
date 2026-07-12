"""Kernel module tests — validates AI kernel components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKernelImports:
    """Test that kernel modules can be imported."""

    def test_kernel_package_imports(self):
        """Kernel package imports successfully."""
        import kernel  # noqa: F401

        assert kernel is not None

    def test_kernel_kernel_imports(self):
        """Kernel main module imports."""
        from kernel import kernel as k  # noqa: F401

        assert k is not None

    def test_kernel_state_imports(self):
        """Kernel state module imports."""
        from kernel import state  # noqa: F401

        assert state is not None

    def test_kernel_session_imports(self):
        """Kernel session module imports."""
        from kernel import session  # noqa: F401

        assert session is not None

    def test_kernel_context_imports(self):
        """Kernel context module imports."""
        from kernel import context  # noqa: F401

        assert context is not None
