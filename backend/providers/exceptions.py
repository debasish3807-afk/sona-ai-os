"""Provider-specific exceptions.

Defines a hierarchy of exceptions for provider operations including
connection failures, rate limiting, authentication errors, and
model-specific issues.
"""

from typing import Any


class ProviderError(Exception):
    """Base exception for all provider errors.

    Attributes:
        message: Human-readable error message.
        provider_id: The provider that raised the error.
        status_code: HTTP status code if applicable.
        error_code: Machine-readable error code.
        details: Additional error context.
        retryable: Whether the operation can be retried.
    """

    def __init__(
        self,
        message: str = "Provider error occurred",
        provider_id: str | None = None,
        status_code: int | None = None,
        error_code: str = "PROVIDER_ERROR",
        details: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        self.message = message
        self.provider_id = provider_id
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.retryable = retryable
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "provider_id": self.provider_id,
            "status_code": self.status_code,
            "retryable": self.retryable,
            "details": self.details,
        }


class ProviderConnectionError(ProviderError):
    """Failed to connect to the provider."""

    def __init__(
        self,
        message: str = "Failed to connect to provider",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            error_code="CONNECTION_ERROR",
            details=details,
            retryable=True,
        )


class ProviderAuthenticationError(ProviderError):
    """Authentication with the provider failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            retryable=False,
        )


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        provider_id: str | None = None,
        retry_after_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if retry_after_seconds is not None:
            _details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=429,
            error_code="RATE_LIMIT_ERROR",
            details=_details,
            retryable=True,
        )
        self.retry_after_seconds = retry_after_seconds


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""

    def __init__(
        self,
        message: str = "Request timed out",
        provider_id: str | None = None,
        timeout_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if timeout_seconds is not None:
            _details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=408,
            error_code="TIMEOUT_ERROR",
            details=_details,
            retryable=True,
        )


class ModelNotFoundError(ProviderError):
    """Requested model not available on the provider."""

    def __init__(
        self,
        message: str = "Model not found",
        provider_id: str | None = None,
        model_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if model_id:
            _details["model_id"] = model_id
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=404,
            error_code="MODEL_NOT_FOUND",
            details=_details,
            retryable=False,
        )


class ModelOverloadedError(ProviderError):
    """Model is temporarily overloaded."""

    def __init__(
        self,
        message: str = "Model overloaded",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=503,
            error_code="MODEL_OVERLOADED",
            details=details,
            retryable=True,
        )


class ContentFilterError(ProviderError):
    """Content was blocked by provider safety filters."""

    def __init__(
        self,
        message: str = "Content filtered by safety policy",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=400,
            error_code="CONTENT_FILTERED",
            details=details,
            retryable=False,
        )


class InvalidRequestError(ProviderError):
    """The request to the provider was malformed."""

    def __init__(
        self,
        message: str = "Invalid request",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=400,
            error_code="INVALID_REQUEST",
            details=details,
            retryable=False,
        )


class QuotaExceededError(ProviderError):
    """Provider usage quota has been exceeded."""

    def __init__(
        self,
        message: str = "Quota exceeded",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=402,
            error_code="QUOTA_EXCEEDED",
            details=details,
            retryable=False,
        )


class ProviderUnavailableError(ProviderError):
    """Provider is currently unavailable."""

    def __init__(
        self,
        message: str = "Provider unavailable",
        provider_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=503,
            error_code="PROVIDER_UNAVAILABLE",
            details=details,
            retryable=True,
        )


class AllProvidersFailed(ProviderError):
    """All providers (including fallbacks) failed to serve the request."""

    def __init__(
        self,
        message: str = "All providers failed",
        attempted_providers: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if attempted_providers:
            _details["attempted_providers"] = attempted_providers
        super().__init__(
            message=message,
            error_code="ALL_PROVIDERS_FAILED",
            details=_details,
            retryable=False,
        )
