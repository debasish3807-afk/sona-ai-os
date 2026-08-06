"""Unit tests for shared kernel domain primitives."""

from datetime import datetime
from uuid import UUID

import pytest

from sona_shared.domain.primitives import (
    DomainEvent,
    Entity,
    EntityId,
    Result,
    Timestamp,
)


class TestEntityId:
    """Tests for the EntityId value object."""

    def test_creates_with_default_uuid(self) -> None:
        entity_id = EntityId()
        assert isinstance(entity_id.value, UUID)

    def test_creates_with_specific_uuid(self) -> None:
        specific_uuid = UUID("12345678-1234-5678-1234-567812345678")
        entity_id = EntityId(value=specific_uuid)
        assert entity_id.value == specific_uuid

    def test_str_returns_uuid_string(self) -> None:
        specific_uuid = UUID("12345678-1234-5678-1234-567812345678")
        entity_id = EntityId(value=specific_uuid)
        assert str(entity_id) == "12345678-1234-5678-1234-567812345678"

    def test_is_frozen(self) -> None:
        entity_id = EntityId()
        with pytest.raises(Exception):
            entity_id.value = UUID("12345678-1234-5678-1234-567812345678")  # type: ignore[misc]

    def test_two_instances_have_different_uuids(self) -> None:
        id1 = EntityId()
        id2 = EntityId()
        assert id1.value != id2.value


class TestTimestamp:
    """Tests for the Timestamp value object."""

    def test_creates_with_default_datetime(self) -> None:
        ts = Timestamp()
        assert isinstance(ts.value, datetime)

    def test_creates_with_specific_datetime(self) -> None:
        specific_time = datetime(2024, 1, 15, 10, 30, 0)
        ts = Timestamp(value=specific_time)
        assert ts.value == specific_time

    def test_is_frozen(self) -> None:
        ts = Timestamp()
        with pytest.raises(Exception):
            ts.value = datetime.now()  # type: ignore[misc]


class TestEntity:
    """Tests for the Entity base class."""

    def test_creates_with_default_fields(self) -> None:
        entity = Entity()
        assert isinstance(entity.id, EntityId)
        assert isinstance(entity.created_at, Timestamp)
        assert isinstance(entity.updated_at, Timestamp)

    def test_creates_with_specific_fields(self) -> None:
        specific_id = EntityId()
        specific_time = Timestamp()
        entity = Entity(id=specific_id, created_at=specific_time, updated_at=specific_time)
        assert entity.id == specific_id
        assert entity.created_at == specific_time
        assert entity.updated_at == specific_time

    def test_is_mutable(self) -> None:
        entity = Entity()
        new_time = Timestamp()
        entity.updated_at = new_time
        assert entity.updated_at == new_time


class TestDomainEvent:
    """Tests for the DomainEvent base class."""

    def test_creates_with_default_fields(self) -> None:
        event = DomainEvent()
        assert isinstance(event.event_id, EntityId)
        assert isinstance(event.occurred_at, Timestamp)
        assert event.aggregate_id is None

    def test_creates_with_aggregate_id(self) -> None:
        agg_id = EntityId()
        event = DomainEvent(aggregate_id=agg_id)
        assert event.aggregate_id == agg_id

    def test_is_frozen(self) -> None:
        event = DomainEvent()
        with pytest.raises(Exception):
            event.event_id = EntityId()  # type: ignore[misc]


class TestResult:
    """Tests for the Result pattern."""

    def test_ok_creates_successful_result(self) -> None:
        result = Result.ok(42)
        assert result.is_success is True
        assert result.value == 42

    def test_fail_creates_failed_result(self) -> None:
        result = Result.fail("something went wrong")
        assert result.is_success is False
        assert result.error == "something went wrong"

    def test_value_raises_on_failed_result(self) -> None:
        result = Result.fail("error")
        with pytest.raises(ValueError, match="Cannot access value of failed Result"):
            _ = result.value

    def test_error_raises_on_successful_result(self) -> None:
        result = Result.ok(42)
        with pytest.raises(ValueError, match="Cannot access error of successful Result"):
            _ = result.error

    def test_ok_with_none_value(self) -> None:
        result = Result.ok(None)
        assert result.is_success is True
        assert result.value is None

    def test_ok_with_complex_value(self) -> None:
        data = {"key": "value", "items": [1, 2, 3]}
        result = Result.ok(data)
        assert result.is_success is True
        assert result.value == data

    def test_fail_with_complex_error(self) -> None:
        error = {"code": 404, "message": "Not found"}
        result = Result.fail(error)
        assert result.is_success is False
        assert result.error == error

    def test_is_frozen(self) -> None:
        result = Result.ok(42)
        with pytest.raises(Exception):
            result._value = 99  # type: ignore[misc]
