"""Document loaders for Knowledge OS.

Provides loaders for various document formats including text, markdown,
HTML, PDF, and GitHub repositories.
"""

from sona_knowledge.infrastructure.loaders.base import DocumentLoader
from sona_knowledge.infrastructure.loaders.github_loader import GitHubLoader
from sona_knowledge.infrastructure.loaders.html_loader import HTMLLoader
from sona_knowledge.infrastructure.loaders.markdown_loader import MarkdownLoader
from sona_knowledge.infrastructure.loaders.pdf_loader import PDFLoader
from sona_knowledge.infrastructure.loaders.text_loader import TextLoader

__all__ = [
    "DocumentLoader",
    "GitHubLoader",
    "HTMLLoader",
    "MarkdownLoader",
    "PDFLoader",
    "TextLoader",
]
