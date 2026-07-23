"""API automation — programmable HTTP client."""

from __future__ import annotations

from typing import Any

import httpx

from config.logging import get_logger

logger = get_logger(__name__)


class APIAutomation:
    def __init__(self, base_url: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        self._cookies: dict[str, str] = {}

    def set_header(self, name: str, value: str) -> None:
        self._headers[name] = value

    def set_cookie(self, name: str, value: str) -> None:
        self._cookies[name] = value

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = self._base_url + path if self._base_url else path
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    method.upper(), url, json=json_body, params=params, headers=self._headers
                )
                result = {
                    "success": resp.status_code < 400,
                    "status_code": resp.status_code,
                    "url": str(resp.url),
                }
                if "application/json" in resp.headers.get("content-type", ""):
                    result["data"] = resp.json()
                else:
                    result["text"] = resp.text[:5000]
                return result
        except Exception as exc:
            return {"success": False, "error": str(exc), "url": url}

    async def get(self, path: str, **params: str) -> dict[str, Any]:
        return await self.request("GET", path, params=params or None)

    async def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("POST", path, json_body=data)

    async def put(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("PUT", path, json_body=data)

    async def delete(self, path: str) -> dict[str, Any]:
        return await self.request("DELETE", path)
