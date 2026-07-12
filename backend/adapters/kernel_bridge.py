"""Kernel Bridge — connects legacy kernel contracts with microkernel runtime."""

from __future__ import annotations

import time
from typing import Any

from adapters.exceptions import BridgeError
from config.logging import get_logger
from microkernel.kernel_core import Microkernel

logger = get_logger(__name__)


class KernelBridge:
    """Bridges legacy kernel contracts with the microkernel runtime.

    Provides a unified interface for routing requests, sanitizing inputs,
    aggregating health status, and emitting events across the boundary.
    """

    def __init__(self, microkernel: Microkernel) -> None:
        self._microkernel = microkernel
        self._request_count: int = 0
        self._event_log: list[dict[str, Any]] = []

    async def route_request(
        self, source: str, destination: str, payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Route a request through the microkernel IPC bus.

        Args:
            source: Originating service identifier.
            destination: Target service identifier.
            payload: Message payload to deliver.

        Returns:
            Response payload or None if delivery failed.
        """
        self._request_count += 1
        try:
            response = await self._microkernel._ipc_bus.request(
                source=source,
                destination=destination,
                payload=payload,
                timeout=10.0,
            )
            if response is not None:
                return response.payload
            return None
        except Exception as exc:
            logger.error(
                "bridge_route_failed",
                source=source,
                destination=destination,
                error=str(exc),
            )
            raise BridgeError(f"route failed: {exc}") from exc

    async def sanitize_input(self, text: str) -> tuple[bool, list[str]]:
        """Sanitize user input using the microkernel's intent sanitizer.

        Args:
            text: Raw user input to sanitize.

        Returns:
            Tuple of (is_safe, list_of_threats).
        """
        result = self._microkernel._intent_sanitizer.sanitize(text)
        return result.safe, result.threats

    def get_system_health(self) -> dict[str, Any]:
        """Aggregate system health from the microkernel health monitor."""
        return self._microkernel._health_monitor.get_summary()

    def get_ipc_stats(self) -> dict[str, Any]:
        """Return IPC bus statistics."""
        return self._microkernel._ipc_bus.get_channel_stats()

    def emit_event(self, event_type: str, source: str, data: dict[str, Any]) -> None:
        """Emit a bridge-level event for observability.

        Args:
            event_type: Category of event.
            source: Originating component.
            data: Event payload.
        """
        event_record: dict[str, Any] = {
            "event_type": event_type,
            "source": source,
            "data": data,
            "timestamp": time.time(),
        }
        self._event_log.append(event_record)
        logger.debug("bridge_event_emitted", event_type=event_type, source=source)
