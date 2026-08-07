"""Unit tests for the CorrelationManager infrastructure module.

Tests cover ID generation, context propagation via contextvars,
header extraction, and header injection.
"""

from sona_observability.infrastructure.correlation import (
    HEADER_REQUEST_ID,
    HEADER_SPAN_ID,
    HEADER_TRACE_ID,
    CorrelationManager,
)


class TestIDGeneration:
    """Tests for correlation ID generation."""

    def test_generate_request_id_is_string(self) -> None:
        """Generated request_id is a non-empty string."""
        rid = CorrelationManager.generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) > 0

    def test_generate_request_id_unique(self) -> None:
        """Each call generates a unique request_id."""
        ids = {CorrelationManager.generate_request_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_trace_id_is_string(self) -> None:
        """Generated trace_id is a non-empty string."""
        tid = CorrelationManager.generate_trace_id()
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_generate_trace_id_unique(self) -> None:
        """Each call generates a unique trace_id."""
        ids = {CorrelationManager.generate_trace_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_span_id_is_string(self) -> None:
        """Generated span_id is a non-empty string."""
        sid = CorrelationManager.generate_span_id()
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_generate_span_id_length(self) -> None:
        """Span ID is 16 characters."""
        sid = CorrelationManager.generate_span_id()
        assert len(sid) == 16


class TestContextPropagation:
    """Tests for context variable propagation."""

    def test_set_and_get_request_id(self) -> None:
        """Can set and get request_id from context."""
        CorrelationManager.set_request_id("req-123")
        assert CorrelationManager.get_request_id() == "req-123"
        CorrelationManager.clear()

    def test_set_and_get_trace_id(self) -> None:
        """Can set and get trace_id from context."""
        CorrelationManager.set_trace_id("trace-abc")
        assert CorrelationManager.get_trace_id() == "trace-abc"
        CorrelationManager.clear()

    def test_set_and_get_span_id(self) -> None:
        """Can set and get span_id from context."""
        CorrelationManager.set_span_id("span-def")
        assert CorrelationManager.get_span_id() == "span-def"
        CorrelationManager.clear()

    def test_clear_resets_all(self) -> None:
        """clear() resets all context vars to empty."""
        CorrelationManager.set_request_id("req-1")
        CorrelationManager.set_trace_id("trace-1")
        CorrelationManager.set_span_id("span-1")
        CorrelationManager.clear()
        assert CorrelationManager.get_request_id() == ""
        assert CorrelationManager.get_trace_id() == ""
        assert CorrelationManager.get_span_id() == ""

    def test_default_values_are_empty(self) -> None:
        """Default context values are empty strings."""
        CorrelationManager.clear()
        assert CorrelationManager.get_request_id() == ""
        assert CorrelationManager.get_trace_id() == ""
        assert CorrelationManager.get_span_id() == ""


class TestHeaderExtraction:
    """Tests for extracting correlation IDs from headers."""

    def test_extract_request_id(self) -> None:
        """Extracts request_id from headers."""
        headers = {HEADER_REQUEST_ID: "req-from-header"}
        result = CorrelationManager.extract_from_headers(headers)
        assert result["request_id"] == "req-from-header"

    def test_extract_trace_id(self) -> None:
        """Extracts trace_id from headers."""
        headers = {HEADER_TRACE_ID: "trace-from-header"}
        result = CorrelationManager.extract_from_headers(headers)
        assert result["trace_id"] == "trace-from-header"

    def test_extract_span_id(self) -> None:
        """Extracts span_id from headers."""
        headers = {HEADER_SPAN_ID: "span-from-header"}
        result = CorrelationManager.extract_from_headers(headers)
        assert result["span_id"] == "span-from-header"

    def test_extract_all_ids(self) -> None:
        """Extracts all correlation IDs from headers."""
        headers = {
            HEADER_REQUEST_ID: "req-1",
            HEADER_TRACE_ID: "trace-1",
            HEADER_SPAN_ID: "span-1",
        }
        result = CorrelationManager.extract_from_headers(headers)
        assert result == {"request_id": "req-1", "trace_id": "trace-1", "span_id": "span-1"}

    def test_extract_empty_headers(self) -> None:
        """Empty headers returns empty dict."""
        result = CorrelationManager.extract_from_headers({})
        assert result == {}

    def test_extract_case_insensitive(self) -> None:
        """Header extraction is case-insensitive."""
        headers = {"X-Request-Id": "req-upper"}
        result = CorrelationManager.extract_from_headers(headers)
        assert result["request_id"] == "req-upper"


class TestHeaderInjection:
    """Tests for injecting correlation IDs into headers."""

    def test_inject_request_id(self) -> None:
        """Injects request_id into headers."""
        CorrelationManager.set_request_id("req-inject")
        headers = CorrelationManager.inject_into_headers()
        assert headers[HEADER_REQUEST_ID] == "req-inject"
        CorrelationManager.clear()

    def test_inject_trace_id(self) -> None:
        """Injects trace_id into headers."""
        CorrelationManager.set_trace_id("trace-inject")
        headers = CorrelationManager.inject_into_headers()
        assert headers[HEADER_TRACE_ID] == "trace-inject"
        CorrelationManager.clear()

    def test_inject_span_id(self) -> None:
        """Injects span_id into headers."""
        CorrelationManager.set_span_id("span-inject")
        headers = CorrelationManager.inject_into_headers()
        assert headers[HEADER_SPAN_ID] == "span-inject"
        CorrelationManager.clear()

    def test_inject_preserves_existing_headers(self) -> None:
        """Injection preserves existing header values."""
        CorrelationManager.set_request_id("req-1")
        headers = CorrelationManager.inject_into_headers({"content-type": "application/json"})
        assert headers["content-type"] == "application/json"
        assert headers[HEADER_REQUEST_ID] == "req-1"
        CorrelationManager.clear()

    def test_inject_skips_empty_values(self) -> None:
        """Injection skips empty correlation values."""
        CorrelationManager.clear()
        headers = CorrelationManager.inject_into_headers()
        assert HEADER_REQUEST_ID not in headers
        assert HEADER_TRACE_ID not in headers
        assert HEADER_SPAN_ID not in headers


class TestInitialize:
    """Tests for initialize method."""

    def test_initialize_generates_ids(self) -> None:
        """Initialize generates request and trace IDs."""
        ids = CorrelationManager.initialize()
        assert "request_id" in ids
        assert "trace_id" in ids
        assert len(ids["request_id"]) > 0
        assert len(ids["trace_id"]) > 0
        CorrelationManager.clear()

    def test_initialize_uses_provided_request_id(self) -> None:
        """Initialize uses provided request_id."""
        ids = CorrelationManager.initialize(request_id="custom-req")
        assert ids["request_id"] == "custom-req"
        assert CorrelationManager.get_request_id() == "custom-req"
        CorrelationManager.clear()

    def test_initialize_uses_provided_trace_id(self) -> None:
        """Initialize uses provided trace_id."""
        ids = CorrelationManager.initialize(trace_id="custom-trace")
        assert ids["trace_id"] == "custom-trace"
        assert CorrelationManager.get_trace_id() == "custom-trace"
        CorrelationManager.clear()

    def test_initialize_sets_context_vars(self) -> None:
        """Initialize sets context vars for later retrieval."""
        CorrelationManager.initialize(request_id="r1", trace_id="t1")
        assert CorrelationManager.get_request_id() == "r1"
        assert CorrelationManager.get_trace_id() == "t1"
        CorrelationManager.clear()
