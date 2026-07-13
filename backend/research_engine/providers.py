"""Real local-first research providers with graceful web failover."""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus

import httpx

from research_engine.models import SourceDocument, SourceKind


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.skip = tag in {"script", "style", "noscript"}

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = False

    def handle_data(self, data: str) -> None:
        if not self.skip and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def clean_html(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def stable_id(provider: str, title: str, url: str | None, text: str) -> str:
    raw = f"{provider}|{title}|{url or ''}|{text[:300]}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


class SearchProvider(ABC):
    kind: SourceKind
    name: str

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        """Return normalized documents or an empty list when unavailable."""


class LocalFileProvider(SearchProvider):
    """Search local markdown, text, and PDF files using real file contents."""

    kind = SourceKind.LOCAL_DOCUMENT
    name = "local_files"

    def __init__(self, roots: list[Path] | None = None) -> None:
        self.roots = roots or [Path(os.getenv("SONA_KNOWLEDGE_DIR", ".")).resolve()]
        self.extensions = {".md", ".txt", ".rst", ".pdf"}

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        terms = [term.lower() for term in re.findall(r"[\w-]+", query) if len(term) > 2]
        results: list[SourceDocument] = []
        for root in self.roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if len(results) >= limit:
                    break
                if not path.is_file() or path.suffix.lower() not in self.extensions:
                    continue
                text = await asyncio.to_thread(self._read_file, path)
                if not text:
                    continue
                lowered = text.lower()
                score = sum(1 for term in terms if term in lowered)
                if score == 0:
                    continue
                kind = (
                    SourceKind.PDF
                    if path.suffix.lower() == ".pdf"
                    else SourceKind.MARKDOWN
                    if path.suffix.lower() == ".md"
                    else SourceKind.LOCAL_DOCUMENT
                )
                results.append(
                    SourceDocument(
                        stable_id(self.name, path.name, str(path), text),
                        path.name,
                        path.as_uri(),
                        kind,
                        text[:8000],
                        self.name,
                        metadata={"path": str(path), "term_hits": score},
                        relevance_score=float(score),
                    )
                )
        return sorted(results, key=lambda item: item.relevance_score, reverse=True)[:limit]

    def _read_file(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            try:
                return path.read_bytes().decode("latin-1", errors="ignore")
            except OSError:
                return ""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""


class HttpJsonProvider(SearchProvider):
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def _get_json(self, url: str, headers: dict[str, str] | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {}


class WikipediaProvider(HttpJsonProvider):
    kind = SourceKind.WIKIPEDIA
    name = "wikipedia"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        try:
            data = await self._get_json(
                f"https://en.wikipedia.org/w/rest.php/v1/search/page?q={quote_plus(query)}&limit={limit}"
            )
        except (httpx.HTTPError, ValueError):
            return []
        docs = []
        for page in data.get("pages", []):
            title = page.get("title", "Wikipedia result")
            text = clean_html(page.get("excerpt", ""))
            url = f"https://en.wikipedia.org/wiki/{quote_plus(str(page.get('key', title)))}"
            docs.append(
                SourceDocument(
                    stable_id(self.name, title, url, text),
                    title,
                    url,
                    self.kind,
                    text,
                    self.name,
                    metadata=page,
                )
            )
        return docs


class ArxivProvider(SearchProvider):
    kind = SourceKind.ARXIV
    name = "arxiv"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&start=0&max_results={limit}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError:
            return []
        entries = re.findall(r"<entry>(.*?)</entry>", response.text, flags=re.S)
        docs = []
        for entry in entries:
            title = clean_html(" ".join(re.findall(r"<title>(.*?)</title>", entry, flags=re.S)))
            summary = clean_html(
                " ".join(re.findall(r"<summary>(.*?)</summary>", entry, flags=re.S))
            )
            link = next(iter(re.findall(r"<id>(.*?)</id>", entry, flags=re.S)), None)
            published = next(iter(re.findall(r"<published>(.*?)</published>", entry)), None)
            date = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None
            docs.append(
                SourceDocument(
                    stable_id(self.name, title, link, summary),
                    title,
                    link,
                    self.kind,
                    summary,
                    self.name,
                    published_at=date,
                )
            )
        return docs


class DuckDuckGoProvider(HttpJsonProvider):
    kind = SourceKind.DUCKDUCKGO
    name = "duckduckgo"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        try:
            data = await self._get_json(
                f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            )
        except (httpx.HTTPError, ValueError):
            return []
        rows = data.get("RelatedTopics", [])[:limit]
        docs = []
        for row in rows:
            if "Topics" in row:
                row = row["Topics"][0] if row["Topics"] else {}
            text = row.get("Text", "")
            url = row.get("FirstURL")
            if text:
                docs.append(
                    SourceDocument(
                        stable_id(self.name, text[:80], url, text),
                        text[:120],
                        url,
                        self.kind,
                        text,
                        self.name,
                    )
                )
        return docs


class BraveProvider(HttpJsonProvider):
    kind = SourceKind.BRAVE
    name = "brave"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        token = os.getenv("BRAVE_SEARCH_API_KEY")
        if not token:
            return []
        try:
            data = await self._get_json(
                f"https://api.search.brave.com/res/v1/web/search?q={quote_plus(query)}&count={limit}",
                {"X-Subscription-Token": token},
            )
        except (httpx.HTTPError, ValueError):
            return []
        docs = []
        for row in data.get("web", {}).get("results", [])[:limit]:
            text = clean_html(row.get("description", ""))
            title = clean_html(row.get("title", "Brave result"))
            url = row.get("url")
            docs.append(
                SourceDocument(
                    stable_id(self.name, title, url, text),
                    title,
                    url,
                    self.kind,
                    text,
                    self.name,
                    metadata=row,
                )
            )
        return docs


class GitHubProvider(HttpJsonProvider):
    kind = SourceKind.GITHUB
    name = "github"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        headers = {"Accept": "application/vnd.github+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            data = await self._get_json(
                f"https://api.github.com/search/repositories?q={quote_plus(query)}&per_page={limit}",
                headers,
            )
        except (httpx.HTTPError, ValueError):
            return []
        docs = []
        for repo in data.get("items", [])[:limit]:
            text = repo.get("description") or ""
            url = repo.get("html_url")
            title = repo.get("full_name", "GitHub repository")
            docs.append(
                SourceDocument(
                    stable_id(self.name, title, url, text),
                    title,
                    url,
                    self.kind,
                    text,
                    self.name,
                    metadata={
                        "stars": repo.get("stargazers_count"),
                        "updated_at": repo.get("updated_at"),
                    },
                )
            )
        return docs
