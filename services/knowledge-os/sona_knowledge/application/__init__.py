"""Knowledge OS application layer.

Contains use cases and port (interface) definitions for the Knowledge OS service.
"""

from sona_knowledge.application.ports import (
    DocumentProcessorPort,
    KnowledgeBasePort,
)

__all__ = [
    "DocumentProcessorPort",
    "KnowledgeBasePort",
]
