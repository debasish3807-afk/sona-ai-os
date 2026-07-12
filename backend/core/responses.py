"""Standardized API response models."""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    All API responses follow this consistent structure.
    """

    success: bool = Field(description="Whether the request was successful")
    data: Optional[T] = Field(default=None, description="Response payload")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp in UTC",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class SuccessResponse(ApiResponse[T], Generic[T]):
    """Successful response with data payload."""

    success: bool = True

    @classmethod
    def create(
        cls,
        data: Any = None,
        message: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "SuccessResponse[Any]":
        """Factory method for creating success responses.

        Args:
            data: Response payload.
            message: Optional human-readable message.
            meta: Optional metadata.

        Returns:
            SuccessResponse instance.
        """
        return cls(data=data, message=message, meta=meta)


class ErrorDetail(BaseModel):
    """Error detail model."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: ErrorDetail = Field(description="Error information")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp in UTC",
    )

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "ErrorResponse":
        """Factory method for creating error responses.

        Args:
            code: Machine-readable error code.
            message: Human-readable error message.
            details: Optional additional details.

        Returns:
            ErrorResponse instance.
        """
        return cls(error=ErrorDetail(code=code, message=message, details=details))


class PaginatedResponse(ApiResponse[List[T]], Generic[T]):
    """Paginated list response."""

    success: bool = True
    pagination: Optional[Dict[str, Any]] = Field(
        default=None, description="Pagination metadata"
    )

    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: Optional[str] = None,
    ) -> "PaginatedResponse[Any]":
        """Factory method for creating paginated responses.

        Args:
            items: List of items for the current page.
            total: Total number of items.
            page: Current page number.
            page_size: Items per page.
            message: Optional message.

        Returns:
            PaginatedResponse instance.
        """
        total_pages = (total + page_size - 1) // page_size
        return cls(
            data=items,
            message=message,
            pagination={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        )
