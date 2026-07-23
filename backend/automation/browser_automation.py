"""Browser automation — programmatic web interaction."""

from __future__ import annotations

import re
from typing import Any

import httpx

from config.logging import get_logger

logger = get_logger(__name__)


class BrowserAutomation:
    def __init__(self) -> None:
        self._url = ""
        self._html = ""
        self._history: list[str] = []

    @property
    def current_url(self) -> str:
        return self._url

    @property
    def page_source(self) -> str:
        return self._html

    async def navigate(self, url: str) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                resp = await client.get(url, headers={"User-Agent": "SonaAIOS/1.0"})
                resp.raise_for_status()
                self._url = str(resp.url)
                self._html = resp.text
                self._history.append(self._url)
                return {
                    "success": True,
                    "url": self._url,
                    "status": resp.status_code,
                    "content_length": len(resp.text),
                }
        except Exception as exc:
            return {"success": False, "error": str(exc), "url": url}

    async def extract_text(self) -> dict[str, Any]:
        text = re.sub(r"<[^>]+>", " ", self._html)
        text = re.sub(r"\s+", " ", text).strip()[:5000]
        return {"success": True, "text": text, "length": len(text)}

    async def extract_links(self) -> dict[str, Any]:
        links = re.findall(r'href=["\'](https?://[^"\']+)["\']', self._html, re.IGNORECASE)
        return {"success": True, "links": links[:50]}

    async def extract_meta(self) -> dict[str, Any]:
        title = re.search(r"<title[^>]*>(.*?)</title>", self._html, re.IGNORECASE)
        return {"success": True, "title": title.group(1).strip() if title else "", "url": self._url}

    def get_history(self) -> list[str]:
        return self._history

    async def screenshot(self) -> dict[str, Any]:
        return {"success": False, "error": "Screenshot requires a real browser"}
