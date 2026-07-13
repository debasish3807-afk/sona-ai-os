"""Shared HTTP client with retry, timeout, and exponential backoff.

All cloud providers use this module to make HTTP requests with
production-grade resilience: automatic retries, circuit breaking,
and detailed logging.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from config.logging import get_logger
from providers.config import ProviderConfig, RetryConfig

logger = get_logger(__name__)


class ProviderHTTPError(Exception):
    """Raised when a provider HTTP request fails after retries."""

    def __init__(self, message: str, status_code: int = 0, provider: str = "") -> None:
        self.status_code = status_code
        self.provider = provider
        super().__init__(message)


class ProviderAuthError(ProviderHTTPError):
    """Raised when API key is missing or rejected."""


class ProviderRateLimitError(ProviderHTTPError):
    """Raised when rate limits are exceeded after retries."""


class ProviderTimeoutError(ProviderHTTPError):
    """Raised when request times out after retries."""


def load_api_key(env_var: str) -> str | None:
    """Load API key from environment variable.

    Args:
        env_var: Name of the environment variable.

    Returns:
        The API key string or None if not set.
    """
    return os.environ.get(env_var)


async def _sleep_with_backoff(attempt: int, retry_config: RetryConfig) -> None:
    """Sleep with exponential backoff between retries."""
    delay = min(
        retry_config.initial_delay_seconds * (retry_config.exponential_base**attempt),
        retry_config.max_delay_seconds,
    )
    await asyncio.sleep(delay)


class ProviderClient:
    """HTTP client with retry and timeout for cloud AI providers.

    Handles:
        - Automatic retries with exponential backoff
        - Request timeouts
        - Rate limit detection (HTTP 429)
        - Authentication errors (HTTP 401/403)
        - Server errors (HTTP 5xx)
        - Connection failures
        - Comprehensive logging
    """

    def __init__(self, config: ProviderConfig, api_key: str | None = None) -> None:
        self._config = config
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        return self._config.base_url.rstrip("/")

    @property
    def api_key(self) -> str | None:
        return self._api_key

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with auth. Override in subclasses for custom auth."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def initialize(self) -> None:
        """Create the HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_headers(),
            timeout=httpx.Timeout(self._config.timeout_seconds, connect=10.0),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._build_headers(),
                timeout=httpx.Timeout(self._config.timeout_seconds, connect=10.0),
            )
        return self._client

    async def post(
        self,
        path: str,
        json_data: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request with retry and backoff.

        Args:
            path: API endpoint path.
            json_data: Request body.
            extra_headers: Additional headers to include.

        Returns:
            Parsed JSON response.

        Raises:
            ProviderAuthError: If authentication fails.
            ProviderRateLimitError: If rate limited after retries.
            ProviderTimeoutError: If request times out.
            ProviderHTTPError: For other HTTP failures.
        """
        client = self._get_client()
        retry_config = self._config.retry
        last_error: Exception | None = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                headers = extra_headers or {}
                resp = await client.post(path, json=json_data, headers=headers)

                if resp.status_code in (401, 403):
                    raise ProviderAuthError(
                        f"Authentication failed: {resp.status_code}",
                        status_code=resp.status_code,
                        provider=self._config.provider_id.value,
                    )

                if resp.status_code == 429:
                    if attempt < retry_config.max_retries:
                        logger.warning(
                            "Rate limited, retrying",
                            provider=self._config.provider_id.value,
                            attempt=attempt + 1,
                        )
                        await _sleep_with_backoff(attempt, retry_config)
                        continue
                    raise ProviderRateLimitError(
                        "Rate limit exceeded after retries",
                        status_code=429,
                        provider=self._config.provider_id.value,
                    )

                if resp.status_code >= 500:
                    if attempt < retry_config.max_retries:
                        logger.warning(
                            "Server error, retrying",
                            provider=self._config.provider_id.value,
                            status=resp.status_code,
                            attempt=attempt + 1,
                        )
                        await _sleep_with_backoff(attempt, retry_config)
                        continue
                    raise ProviderHTTPError(
                        f"Server error: {resp.status_code} {resp.text[:200]}",
                        status_code=resp.status_code,
                        provider=self._config.provider_id.value,
                    )

                if resp.status_code >= 400:
                    raise ProviderHTTPError(
                        f"Request failed: {resp.status_code} {resp.text[:200]}",
                        status_code=resp.status_code,
                        provider=self._config.provider_id.value,
                    )

                return resp.json()  # type: ignore[no-any-return]

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < retry_config.max_retries:
                    logger.warning(
                        "Request timeout, retrying",
                        provider=self._config.provider_id.value,
                        attempt=attempt + 1,
                    )
                    await _sleep_with_backoff(attempt, retry_config)
                    continue

            except httpx.ConnectError as exc:
                last_error = exc
                if attempt < retry_config.max_retries:
                    logger.warning(
                        "Connection failed, retrying",
                        provider=self._config.provider_id.value,
                        attempt=attempt + 1,
                    )
                    await _sleep_with_backoff(attempt, retry_config)
                    continue

            except (ProviderAuthError, ProviderRateLimitError, ProviderHTTPError):
                raise

        # All retries exhausted
        if isinstance(last_error, httpx.TimeoutException):
            raise ProviderTimeoutError(
                f"Request timed out after {retry_config.max_retries} retries",
                provider=self._config.provider_id.value,
            )
        raise ProviderHTTPError(
            f"Request failed after {retry_config.max_retries} retries: {last_error}",
            provider=self._config.provider_id.value,
        )

    async def post_stream(
        self,
        path: str,
        json_data: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a streaming POST request (no retry — streams are not retriable).

        Args:
            path: API endpoint path.
            json_data: Request body.
            extra_headers: Additional headers.

        Returns:
            The httpx.Response for streaming iteration.
        """
        client = self._get_client()
        headers = extra_headers or {}
        return await client.send(
            client.build_request("POST", path, json=json_data, headers=headers),
            stream=True,
        )

    async def get(self, path: str) -> dict[str, Any]:
        """Make a GET request with retry.

        Args:
            path: API endpoint path.

        Returns:
            Parsed JSON response.
        """
        client = self._get_client()
        retry_config = self._config.retry

        for attempt in range(retry_config.max_retries + 1):
            try:
                resp = await client.get(path)
                if resp.status_code >= 500 and attempt < retry_config.max_retries:
                    await _sleep_with_backoff(attempt, retry_config)
                    continue
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < retry_config.max_retries:
                    await _sleep_with_backoff(attempt, retry_config)
                    continue
                raise

        raise ProviderHTTPError(
            "GET request failed after retries",
            provider=self._config.provider_id.value,
        )

    async def health_check(self, path: str = "/models") -> bool:
        """Lightweight health check by hitting a read endpoint.

        Args:
            path: Endpoint to ping.

        Returns:
            True if provider responds successfully.
        """
        client = self._get_client()
        try:
            resp = await client.get(path, timeout=10.0)
            return bool(resp.status_code < 400)
        except (httpx.TimeoutException, httpx.ConnectError):
            return False
