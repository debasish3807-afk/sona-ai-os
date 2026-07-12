"""Exception hierarchy for the adapters layer."""

from __future__ import annotations


class AdapterError(Exception):
    """Base error for all adapter operations."""

    def __init__(self, message: str, adapter: str = "unknown") -> None:
        self.message = message
        self.adapter = adapter
        super().__init__(f"[{adapter}] {message}")


class BootError(AdapterError):
    """Error raised during boot sequence."""

    def __init__(self, message: str, adapter: str = "boot_manager") -> None:
        super().__init__(message, adapter)


class RegistryError(AdapterError):
    """Error raised during service registry operations."""

    def __init__(self, message: str, adapter: str = "runtime_registry") -> None:
        super().__init__(message, adapter)


class PersistenceError(AdapterError):
    """Error raised during persistence operations."""

    def __init__(self, message: str, adapter: str = "persistence") -> None:
        super().__init__(message, adapter)


class BridgeError(AdapterError):
    """Error raised during kernel bridge operations."""

    def __init__(self, message: str, adapter: str = "kernel_bridge") -> None:
        super().__init__(message, adapter)
