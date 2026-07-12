"""Capability Fabric exceptions — failure classification."""

from __future__ import annotations


class CapabilityError(Exception):
    """Base exception for all capability fabric errors."""

    def __init__(self, message: str = "Capability error") -> None:
        super().__init__(message)


class CapabilityNotFoundError(CapabilityError):
    """Raised when a requested capability does not exist in the registry."""

    def __init__(self, capability_id: str = "") -> None:
        msg = f"Capability not found: {capability_id}" if capability_id else "Capability not found"
        super().__init__(msg)


class CapabilityConflictError(CapabilityError):
    """Raised when a capability conflicts with an existing registration."""

    def __init__(self, message: str = "Capability conflict detected") -> None:
        super().__init__(message)


class DependencyError(CapabilityError):
    """Raised when a dependency cannot be resolved or contains cycles."""

    def __init__(self, message: str = "Dependency resolution failed") -> None:
        super().__init__(message)


class SandboxViolationError(CapabilityError):
    """Raised when a capability violates sandbox restrictions."""

    def __init__(self, message: str = "Sandbox policy violation") -> None:
        super().__init__(message)


class CapabilityLoadError(CapabilityError):
    """Raised when a capability fails to load or initialize."""

    def __init__(self, message: str = "Failed to load capability") -> None:
        super().__init__(message)
