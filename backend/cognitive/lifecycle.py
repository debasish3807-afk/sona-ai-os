"""Kernel Lifecycle — manages startup, shutdown, and state transitions."""

from __future__ import annotations

from enum import Enum


class KernelState(str, Enum):
    """Kernel runtime states."""

    STARTING = "starting"
    READY = "ready"
    PROCESSING = "processing"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


VALID_TRANSITIONS: dict[KernelState, set[KernelState]] = {
    KernelState.STARTING: {KernelState.READY, KernelState.STOPPED},
    KernelState.READY: {KernelState.PROCESSING, KernelState.PAUSED, KernelState.SHUTTING_DOWN},
    KernelState.PROCESSING: {KernelState.READY, KernelState.PAUSED, KernelState.SHUTTING_DOWN},
    KernelState.PAUSED: {KernelState.READY, KernelState.SHUTTING_DOWN},
    KernelState.SHUTTING_DOWN: {KernelState.STOPPED},
    KernelState.STOPPED: set(),
}


def can_transition(current: KernelState, target: KernelState) -> bool:
    """Check if a state transition is valid."""
    return target in VALID_TRANSITIONS.get(current, set())
