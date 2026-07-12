"""Browser Tool — fetch web content, extract text, convert to markdown.

Provides safe web content retrieval with:
    - URL fetching with timeout
    - HTML to plain text extraction
    - HTML to markdown conversion
    - Content length limiting
    - Network permission checking
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions


def _html_to_text(html: str) -> str:
    """Strip HTML tags and decode entities for plain text extraction."""
    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Convert common block elements to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr|blockquote)>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _html_to_markdown(html: str) -> str:
    """Convert HTML to basic markdown representation."""
    md = html
    # Remove script/style
    md = re.sub(r"<script[^>]*>.*?</script>", "", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<style[^>]*>.*?</style>", "", md, flags=re.DOTALL | re.IGNORECASE)
    # Headings
    for i in range(1, 7):
        md = re.sub(
            rf"<h{i}[^>]*>(.*?)</h{i}>", rf"{'#' * i} \1\n", md, flags=re.DOTALL | re.IGNORECASE
        )
    # Bold / italic
    md = re.sub(r"<(strong|b)>(.*?)</\1>", r"**\2**", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<(em|i)>(.*?)</\1>", r"*\2*", md, flags=re.DOTALL | re.IGNORECASE)
    # Links
    md = re.sub(
        r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", md, flags=re.DOTALL | re.IGNORECASE
    )
    # Code blocks
    md = re.sub(
        r"<pre[^>]*><code[^>]*>(.*?)</code></pre>",
        r"```\n\1\n```",
        md,
        flags=re.DOTALL | re.IGNORECASE,
    )
    md = re.sub(r"<code>(.*?)</code>", r"`\1`", md, flags=re.DOTALL | re.IGNORECASE)
    # List items
    md = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", md, flags=re.DOTALL | re.IGNORECASE)
    # Paragraphs and breaks
    md = re.sub(r"<br\s*/?>", "\n", md, flags=re.IGNORECASE)
    md = re.sub(r"</(p|div|blockquote)>", "\n\n", md, flags=re.IGNORECASE)
    # Strip remaining tags
    md = re.sub(r"<[^>]+>", "", md)
    # Decode entities
    md = md.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    md = md.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Clean up whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


class BrowserFetchTool(BaseTool):
    """Fetch a URL and return its content."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="browser_fetch",
            description="Fetch a URL and return content as text or markdown",
            category=ToolCategory.BROWSER,
            parameters=[
                ToolParam("url", "string", "The URL to fetch"),
                ToolParam(
                    "format",
                    "string",
                    "Output format: text, markdown, or html",
                    required=False,
                    default="markdown",
                ),
                ToolParam(
                    "max_length",
                    "integer",
                    "Max content length in chars",
                    required=False,
                    default=50000,
                ),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        url = str(params.get("url", ""))
        output_format = str(params.get("format", "markdown"))
        max_length = int(params.get("max_length", 50000))

        if not url:
            return ToolResult(success=False, error="Parameter 'url' is required")

        if not self._permissions.allow_network:
            return ToolResult(success=False, error="Network access is disabled")

        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                headers={"User-Agent": "SonaAIOS/0.8 (Browser Tool)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"Request timed out: {url}")
        except httpx.HTTPStatusError as exc:
            return ToolResult(success=False, error=f"HTTP {exc.response.status_code}: {url}")
        except httpx.ConnectError:
            return ToolResult(success=False, error=f"Connection failed: {url}")
        except Exception as exc:
            return ToolResult(success=False, error=f"Fetch failed: {exc}")

        content_type = resp.headers.get("content-type", "")
        raw_html = resp.text

        # Convert based on requested format
        if output_format == "html":
            output = raw_html
        elif output_format == "text":
            output = _html_to_text(raw_html)
        else:
            output = _html_to_markdown(raw_html) if "text/html" in content_type else raw_html

        # Truncate if needed
        if len(output) > max_length:
            output = output[:max_length] + "\n\n[... content truncated ...]"

        return ToolResult(
            success=True,
            output=output,
            data={
                "url": str(resp.url),
                "status_code": resp.status_code,
                "content_type": content_type,
                "content_length": len(output),
            },
        )


class BrowserSearchTool(BaseTool):
    """Search the web using DuckDuckGo instant answers."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="browser_search",
            description="Search the web and return results (uses DuckDuckGo)",
            category=ToolCategory.BROWSER,
            parameters=[
                ToolParam("query", "string", "Search query"),
                ToolParam("max_results", "integer", "Max results", required=False, default=5),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        query = str(params.get("query", ""))
        max_results = int(params.get("max_results", 5))

        if not query:
            return ToolResult(success=False, error="Parameter 'query' is required")

        if not self._permissions.allow_network:
            return ToolResult(success=False, error="Network access is disabled")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                )
                resp.raise_for_status()
        except Exception as exc:
            return ToolResult(success=False, error=f"Search failed: {exc}")

        data = resp.json()
        results: list[str] = []

        # Abstract (instant answer)
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append(f"**Summary:** {abstract}")
            source = data.get("AbstractSource", "")
            url = data.get("AbstractURL", "")
            if source:
                results.append(f"Source: {source} ({url})")
            results.append("")

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in topic:
                text = topic["Text"]
                first_url = topic.get("FirstURL", "")
                results.append(f"- {text}")
                if first_url:
                    results.append(f"  {first_url}")

        output = "\n".join(results) if results else "No results found"
        return ToolResult(
            success=True,
            output=output,
            data={"query": query, "has_abstract": bool(abstract), "results_count": len(results)},
        )


def register_browser_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all browser tool instances."""
    return [
        BrowserFetchTool(permissions),
        BrowserSearchTool(permissions),
    ]
