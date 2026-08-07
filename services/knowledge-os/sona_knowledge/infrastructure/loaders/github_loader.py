"""GitHub repository document loader."""

import uuid

import structlog

from sona_knowledge.domain.models import Document, DocumentType
from sona_knowledge.infrastructure.loaders.base import DocumentLoader

logger = structlog.get_logger()


class GitHubLoader(DocumentLoader):
    """Loader for GitHub repository content.

    Simulates loading content from GitHub URLs. In production, this
    would use the GitHub API or git clone to fetch content.
    """

    async def load(self, source: str, **kwargs: object) -> Document:
        """Load content from a GitHub URL.

        Args:
            source: GitHub URL or pre-fetched content.
            **kwargs: Optional 'title', 'doc_id', 'content' overrides.

        Returns:
            A Document with the GitHub content.
        """
        content = str(kwargs.get("content", "")) or source
        title = str(kwargs.get("title", "")) or self._extract_repo_name(source)
        doc_id = str(kwargs.get("doc_id", "")) or str(uuid.uuid4())
        doc_type = self._detect_type(source)

        logger.info(
            "loading_github_document",
            title=title,
            url=source,
            doc_type=doc_type,
        )

        return Document(
            id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            metadata={
                "source": "github",
                "url": source,
                "word_count": len(content.split()),
            },
            source_url=source,
        )

    def supports(self, source: str) -> bool:
        """Check if source is a GitHub URL."""
        return "github.com" in source or "raw.githubusercontent.com" in source

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from GitHub URL."""
        parts = url.rstrip("/").split("/")
        # Try to get repo name from URL structure
        for i, part in enumerate(parts):
            if part in ("github.com", "raw.githubusercontent.com"):
                if i + 2 < len(parts):
                    return f"{parts[i + 1]}/{parts[i + 2]}"
        return parts[-1] if parts else "Unknown Repo"

    def _detect_type(self, url: str) -> DocumentType:
        """Detect document type from URL file extension."""
        lower = url.lower()
        if lower.endswith(".md"):
            return DocumentType.MARKDOWN
        if lower.endswith(".html") or lower.endswith(".htm"):
            return DocumentType.HTML
        if lower.endswith(".pdf"):
            return DocumentType.PDF
        if any(lower.endswith(ext) for ext in (".py", ".js", ".ts", ".java", ".go", ".rs")):
            return DocumentType.CODE
        if lower.endswith(".json"):
            return DocumentType.JSON
        return DocumentType.TEXT
