"""Tests for Knowledge OS domain events."""

from dataclasses import FrozenInstanceError

import pytest

from sona_knowledge.domain.events import (
    DocumentDeletedEvent,
    DocumentIngestedEvent,
    IndexingCompletedEvent,
    QueryExecutedEvent,
)


class TestDocumentIngestedEvent:
    """Tests for DocumentIngestedEvent."""

    def test_create_with_defaults(self) -> None:
        event = DocumentIngestedEvent()
        assert event.document_id == ""
        assert event.kb_id == ""
        assert event.chunks_count == 0
        assert event.doc_type == ""

    def test_create_with_values(self) -> None:
        event = DocumentIngestedEvent(
            document_id="doc-1",
            kb_id="kb-main",
            chunks_count=10,
            doc_type="markdown",
        )
        assert event.document_id == "doc-1"
        assert event.kb_id == "kb-main"
        assert event.chunks_count == 10
        assert event.doc_type == "markdown"

    def test_is_frozen(self) -> None:
        event = DocumentIngestedEvent(document_id="doc-1")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.document_id = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        event = DocumentIngestedEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = DocumentIngestedEvent()
        assert event.occurred_at is not None

    def test_two_events_have_different_ids(self) -> None:
        e1 = DocumentIngestedEvent(document_id="doc-1")
        e2 = DocumentIngestedEvent(document_id="doc-2")
        assert e1.event_id != e2.event_id


class TestDocumentDeletedEvent:
    """Tests for DocumentDeletedEvent."""

    def test_create_with_defaults(self) -> None:
        event = DocumentDeletedEvent()
        assert event.document_id == ""

    def test_create_with_value(self) -> None:
        event = DocumentDeletedEvent(document_id="doc-123")
        assert event.document_id == "doc-123"

    def test_is_frozen(self) -> None:
        event = DocumentDeletedEvent(document_id="doc-1")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.document_id = "x"  # type: ignore[misc]

    def test_inherits_domain_event(self) -> None:
        event = DocumentDeletedEvent()
        assert hasattr(event, "event_id")
        assert hasattr(event, "occurred_at")


class TestQueryExecutedEvent:
    """Tests for QueryExecutedEvent."""

    def test_create_with_defaults(self) -> None:
        event = QueryExecutedEvent()
        assert event.query == ""
        assert event.results_count == 0
        assert event.confidence == 0.0

    def test_create_with_values(self) -> None:
        event = QueryExecutedEvent(
            query="What is Python?",
            results_count=5,
            confidence=0.85,
        )
        assert event.query == "What is Python?"
        assert event.results_count == 5
        assert event.confidence == 0.85

    def test_is_frozen(self) -> None:
        event = QueryExecutedEvent(query="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.query = "changed"  # type: ignore[misc]


class TestIndexingCompletedEvent:
    """Tests for IndexingCompletedEvent."""

    def test_create_with_defaults(self) -> None:
        event = IndexingCompletedEvent()
        assert event.kb_id == ""
        assert event.documents_indexed == 0
        assert event.chunks_indexed == 0

    def test_create_with_values(self) -> None:
        event = IndexingCompletedEvent(
            kb_id="kb-prod",
            documents_indexed=50,
            chunks_indexed=350,
        )
        assert event.kb_id == "kb-prod"
        assert event.documents_indexed == 50
        assert event.chunks_indexed == 350

    def test_is_frozen(self) -> None:
        event = IndexingCompletedEvent(kb_id="kb")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.kb_id = "changed"  # type: ignore[misc]
