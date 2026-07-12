"""Core module - shared utilities, exceptions, response models, DI, pipeline, and observability."""

from core.constants import API_VERSION, APP_NAME
from core.container import Container, get_container
from core.exceptions import (
    AppException,
    BadRequestError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from core.observability import RequestTracer, UnifiedHealthMonitor, UnifiedMetrics
from core.pipeline import Pipeline, PipelineRequest, PipelineResult, PipelineStatus
from core.responses import ApiResponse, ErrorResponse, SuccessResponse

__all__ = [
    "API_VERSION",
    "APP_NAME",
    "ApiResponse",
    "AppException",
    "BadRequestError",
    "Container",
    "ErrorResponse",
    "ForbiddenError",
    "InternalServerError",
    "NotFoundError",
    "Pipeline",
    "PipelineRequest",
    "PipelineResult",
    "PipelineStatus",
    "RequestTracer",
    "SuccessResponse",
    "UnauthorizedError",
    "UnifiedHealthMonitor",
    "UnifiedMetrics",
    "ValidationError",
    "get_container",
]
