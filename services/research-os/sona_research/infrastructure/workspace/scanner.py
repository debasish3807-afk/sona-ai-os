"""Workspace scanner for document discovery.

Scans a directory for documents, detecting format from extension
and extracting metadata.
"""

import structlog

from sona_research.domain.workspace_models import DocumentFormat, WorkspaceDocument

logger = structlog.get_logger()

# Extension to format mapping
_EXTENSION_MAP: dict[str, DocumentFormat] = {
    ".md": DocumentFormat.MARKDOWN,
    ".markdown": DocumentFormat.MARKDOWN,
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".txt": DocumentFormat.TEXT,
    ".text": DocumentFormat.TEXT,
    ".py": DocumentFormat.SOURCE_CODE,
    ".js": DocumentFormat.SOURCE_CODE,
    ".ts": DocumentFormat.SOURCE_CODE,
    ".java": DocumentFormat.SOURCE_CODE,
    ".kt": DocumentFormat.SOURCE_CODE,
    ".rs": DocumentFormat.SOURCE_CODE,
    ".go": DocumentFormat.SOURCE_CODE,
    ".rb": DocumentFormat.SOURCE_CODE,
    ".c": DocumentFormat.SOURCE_CODE,
    ".cpp": DocumentFormat.SOURCE_CODE,
    ".h": DocumentFormat.SOURCE_CODE,
    ".json": DocumentFormat.JSON,
    ".yaml": DocumentFormat.YAML,
    ".yml": DocumentFormat.YAML,
}


def detect_format(path: str) -> DocumentFormat:
    """Detect document format from file extension.

    Args:
        path: File path to detect format from.

    Returns:
        The detected DocumentFormat, defaults to TEXT for unknown extensions.
    """
    for ext, fmt in _EXTENSION_MAP.items():
        if path.endswith(ext):
            return fmt
    return DocumentFormat.TEXT


def extract_title(path: str) -> str:
    """Extract a title from a file path.

    Args:
        path: File path to extract title from.

    Returns:
        The filename without extension as a title.
    """
    parts = path.replace("\\", "/").split("/")
    filename = parts[-1] if parts else path
    # Remove extension
    if "." in filename:
        filename = filename.rsplit(".", 1)[0]
    return filename.replace("_", " ").replace("-", " ").title()


class WorkspaceScanner:
    """Scan a workspace directory for documents.

    Uses a simulated filesystem for testing without requiring
    actual file I/O.
    """

    def __init__(self) -> None:
        """Initialize the workspace scanner."""
        self._files: dict[str, str] = {}
        self._metadata: dict[str, dict[str, int | str]] = {}

    def add_file(
        self,
        path: str,
        content: str,
        size_bytes: int = 0,
        last_modified: str = "",
    ) -> None:
        """Add a file to the simulated workspace.

        Args:
            path: File path.
            content: File content.
            size_bytes: File size in bytes (auto-calculated if 0).
            last_modified: Last modification timestamp.
        """
        self._files[path] = content
        self._metadata[path] = {
            "size_bytes": size_bytes or len(content.encode()),
            "last_modified": last_modified,
        }

    async def scan(self, root_path: str = "/") -> list[WorkspaceDocument]:
        """Scan the workspace for documents.

        Args:
            root_path: Root path to scan from. Files matching this prefix
                       are included.

        Returns:
            List of WorkspaceDocument instances found.
        """
        logger.info("workspace_scanner.scan", root_path=root_path)
        documents: list[WorkspaceDocument] = []

        for path, content in sorted(self._files.items()):
            if not path.startswith(root_path):
                continue

            fmt = detect_format(path)
            meta = self._metadata.get(path, {})
            size = int(meta.get("size_bytes", len(content.encode())))
            modified = str(meta.get("last_modified", ""))

            doc = WorkspaceDocument(
                path=path,
                title=extract_title(path),
                content=content,
                format=fmt,
                size_bytes=size,
                last_modified=modified,
            )
            documents.append(doc)

        logger.info(
            "workspace_scanner.scan_complete",
            documents_found=len(documents),
        )
        return documents

    async def scan_by_format(
        self, root_path: str = "/", formats: list[DocumentFormat] | None = None
    ) -> list[WorkspaceDocument]:
        """Scan workspace filtering by document format.

        Args:
            root_path: Root path to scan from.
            formats: List of formats to include. None means all formats.

        Returns:
            Filtered list of WorkspaceDocument instances.
        """
        all_docs = await self.scan(root_path)
        if formats is None:
            return all_docs
        return [doc for doc in all_docs if doc.format in formats]
