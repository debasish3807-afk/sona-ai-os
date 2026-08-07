"""Brain OS infrastructure layer.

Contains concrete adapter implementations for the Brain OS ports.
Adapters connect to external systems (AI Kernel, Memory OS, Workforce OS, etc.)
to fulfill the contracts defined in the application layer.
"""

from sona_brain.infrastructure.brain_runtime import BrainRuntime
from sona_brain.infrastructure.di import create_brain_runtime

__all__ = [
    "BrainRuntime",
    "create_brain_runtime",
]
