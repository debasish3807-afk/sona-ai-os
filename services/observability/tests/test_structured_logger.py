"""Unit tests for the StructuredLogger infrastructure module.

Tests cover JSON output, context binding, enrichment methods,
log sampling, and LoggingPort interface compliance.
"""

from sona_observability.application.ports import LoggingPort
from sona_observability.domain.models import LogLevel
from sona_observability.infrastructure.structured_logger import StructuredLogger


class TestLoggerInterface:
    """Verify StructuredLogger implements LoggingPort."""

    def test_implements_logging_port(self) -> None:
        """StructuredLogger should implement LoggingPort."""
        logger = StructuredLogger()
        assert isinstance(logger, LoggingPort)

    def test_with_context_returns_logging_port(self) -> None:
        """with_context should return a LoggingPort."""
        logger = StructuredLogger()
        scoped = logger.with_context(service="test")
        assert isinstance(scoped, LoggingPort)


class TestBasicLogging:
    """Tests for basic log entry creation."""

    def test_log_creates_entry(self) -> None:
        """Logging creates a captured entry."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "Test message")
        assert len(logger.entries) == 1

    def test_log_entry_has_message(self) -> None:
        """Log entry contains the message."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "Hello world")
        assert logger.entries[0]["message"] == "Hello world"

    def test_log_entry_has_level(self) -> None:
        """Log entry contains the log level."""
        logger = StructuredLogger()
        logger.log(LogLevel.ERROR, "Error occurred")
        assert logger.entries[0]["level"] == "error"

    def test_log_entry_has_timestamp(self) -> None:
        """Log entry contains a timestamp."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "test")
        assert "timestamp" in logger.entries[0]
        assert isinstance(logger.entries[0]["timestamp"], float)

    def test_log_entry_has_service(self) -> None:
        """Log entry contains the service name."""
        logger = StructuredLogger(service_name="my-service")
        logger.log(LogLevel.INFO, "test")
        assert logger.entries[0]["service"] == "my-service"

    def test_default_service_name(self) -> None:
        """Default service name is 'sona-ai-os'."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "test")
        assert logger.entries[0]["service"] == "sona-ai-os"

    def test_all_log_levels(self) -> None:
        """All log levels produce entries."""
        logger = StructuredLogger()
        for level in LogLevel:
            logger.log(level, f"Message at {level}")
        assert len(logger.entries) == 5

    def test_log_with_context(self) -> None:
        """Log with context data merges into entry."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "test", context={"request_id": "req-123"})
        assert logger.entries[0]["request_id"] == "req-123"

    def test_log_context_does_not_overwrite_base_fields(self) -> None:
        """Context data extends but the entry still has base fields."""
        logger = StructuredLogger()
        logger.log(LogLevel.INFO, "test", context={"extra": "value"})
        entry = logger.entries[0]
        assert "timestamp" in entry
        assert "level" in entry
        assert "service" in entry
        assert "extra" in entry


class TestContextBinding:
    """Tests for context binding with with_context."""

    def test_with_context_binds_fields(self) -> None:
        """with_context binds fields to subsequent logs."""
        logger = StructuredLogger()
        scoped = logger.with_context(request_id="req-abc")
        scoped.log(LogLevel.INFO, "test")
        assert logger.entries[0]["request_id"] == "req-abc"

    def test_with_context_multiple_fields(self) -> None:
        """with_context can bind multiple fields."""
        logger = StructuredLogger()
        scoped = logger.with_context(trace_id="t1", span_id="s1", user="admin")
        scoped.log(LogLevel.INFO, "test")
        entry = logger.entries[0]
        assert entry["trace_id"] == "t1"
        assert entry["span_id"] == "s1"
        assert entry["user"] == "admin"

    def test_with_context_chaining(self) -> None:
        """with_context can be chained."""
        logger = StructuredLogger()
        scoped = logger.with_context(a="1").with_context(b="2")
        scoped.log(LogLevel.INFO, "test")
        entry = logger.entries[0]
        assert entry["a"] == "1"
        assert entry["b"] == "2"

    def test_with_context_does_not_modify_original(self) -> None:
        """with_context returns new instance, doesn't modify original."""
        logger = StructuredLogger()
        _ = logger.with_context(extra="value")
        logger.log(LogLevel.INFO, "from original")
        assert "extra" not in logger.entries[0]

    def test_with_context_returns_structured_logger(self) -> None:
        """with_context returns StructuredLogger (covariant return)."""
        logger = StructuredLogger()
        scoped = logger.with_context(x="y")
        assert isinstance(scoped, StructuredLogger)


class TestEnrichment:
    """Tests for enrichment methods."""

    def test_with_request_id(self) -> None:
        """with_request_id adds request_id to context."""
        logger = StructuredLogger()
        scoped = logger.with_request_id("req-xyz")
        scoped.log(LogLevel.INFO, "test")
        assert logger.entries[0]["request_id"] == "req-xyz"

    def test_with_user_id(self) -> None:
        """with_user_id adds user_id to context."""
        logger = StructuredLogger()
        scoped = logger.with_user_id("user-123")
        scoped.log(LogLevel.INFO, "test")
        assert logger.entries[0]["user_id"] == "user-123"

    def test_with_trace(self) -> None:
        """with_trace adds trace_id and span_id to context."""
        logger = StructuredLogger()
        scoped = logger.with_trace("trace-abc", "span-def")
        scoped.log(LogLevel.INFO, "test")
        entry = logger.entries[0]
        assert entry["trace_id"] == "trace-abc"
        assert entry["span_id"] == "span-def"

    def test_enrichment_chaining(self) -> None:
        """Multiple enrichment methods can be chained."""
        logger = StructuredLogger()
        scoped = logger.with_request_id("req-1").with_user_id("usr-2").with_trace("t1", "s1")
        scoped.log(LogLevel.INFO, "test")
        entry = logger.entries[0]
        assert entry["request_id"] == "req-1"
        assert entry["user_id"] == "usr-2"
        assert entry["trace_id"] == "t1"
        assert entry["span_id"] == "s1"


class TestLogSampling:
    """Tests for log sampling."""

    def test_sample_rate_1_logs_all(self) -> None:
        """Sample rate 1.0 logs all messages."""
        logger = StructuredLogger(sample_rate=1.0)
        for _ in range(100):
            logger.log(LogLevel.INFO, "test")
        assert len(logger.entries) == 100

    def test_sample_rate_0_logs_none(self) -> None:
        """Sample rate 0.0 logs no messages."""
        logger = StructuredLogger(sample_rate=0.0)
        for _ in range(100):
            logger.log(LogLevel.INFO, "test")
        assert len(logger.entries) == 0

    def test_sample_rate_property(self) -> None:
        """sample_rate property returns configured rate."""
        logger = StructuredLogger(sample_rate=0.5)
        assert logger.sample_rate == 0.5

    def test_sample_rate_clamped_high(self) -> None:
        """Sample rate above 1.0 is clamped to 1.0."""
        logger = StructuredLogger(sample_rate=2.0)
        assert logger.sample_rate == 1.0

    def test_sample_rate_clamped_low(self) -> None:
        """Sample rate below 0.0 is clamped to 0.0."""
        logger = StructuredLogger(sample_rate=-1.0)
        assert logger.sample_rate == 0.0


class TestSink:
    """Tests for the output sink."""

    def test_sink_receives_json(self) -> None:
        """Sink receives JSON-formatted log entry."""
        output: list[str] = []
        logger = StructuredLogger(sink=output.append)
        logger.log(LogLevel.INFO, "test message")
        assert len(output) == 1
        import json

        parsed = json.loads(output[0])
        assert parsed["message"] == "test message"

    def test_sink_receives_all_fields(self) -> None:
        """Sink output includes all expected fields."""
        output: list[str] = []
        logger = StructuredLogger(service_name="test-svc", sink=output.append)
        logger.log(LogLevel.ERROR, "failure", context={"code": 500})
        import json

        parsed = json.loads(output[0])
        assert parsed["service"] == "test-svc"
        assert parsed["level"] == "error"
        assert parsed["code"] == 500
