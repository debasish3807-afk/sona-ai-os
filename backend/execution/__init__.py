"""Execution Engine — runs plans with retry, rollback, and safety controls.

Executes tool chains sequentially or in parallel with dependency
resolution, timeout handling, and comprehensive result tracking.
"""

from execution.engine import ExecutionEngine, ExecutionResult

__all__ = [
    "ExecutionEngine",
    "ExecutionResult",
]
