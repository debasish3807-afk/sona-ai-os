"""Pipeline module for end-to-end AI request orchestration.

Connects the Gateway to THALAMUS (routing), Brain OS (execution),
Memory OS (context), and AI Kernel (inference).
"""

from app.pipeline.context_injector import ContextInjector
from app.pipeline.error_handler import PipelineErrorHandler
from app.pipeline.metrics import MetricsCollector, PipelineMetrics
from app.pipeline.orchestrator import PipelineContext, PipelineOrchestrator, PipelineResult
from app.pipeline.session import SessionManager
from app.pipeline.streaming import sse_generator, stream_chat_response

__all__ = [
    "ContextInjector",
    "MetricsCollector",
    "PipelineContext",
    "PipelineErrorHandler",
    "PipelineMetrics",
    "PipelineOrchestrator",
    "PipelineResult",
    "SessionManager",
    "sse_generator",
    "stream_chat_response",
]
