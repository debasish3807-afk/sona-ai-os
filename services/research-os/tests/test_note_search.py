"""Tests for note search and filtering."""

import pytest

from sona_research.domain.personal_models import NoteType
from sona_research.infrastructure.notes.runtime import NotesRuntime


@pytest.fixture
async def runtime_with_notes() -> NotesRuntime:
    rt = NotesRuntime()
    await rt.create_note(
        "Python Basics", "Learn variables and loops", NoteType.STRUCTURED, ["python", "learning"]
    )
    await rt.create_note(
        "Meeting: Sprint Planning", "Discussed priorities", NoteType.MEETING, ["work", "sprint"]
    )
    await rt.create_note(
        "Decision: Use PostgreSQL",
        "Chose Postgres for ACID",
        NoteType.DECISION,
        ["architecture", "database"],
    )
    await rt.create_note(
        "Quick thought on testing", "Should use pytest", NoteType.QUICK, ["python", "testing"]
    )
    await rt.create_note(
        "Journal Entry", "Today worked on API design", NoteType.JOURNAL, ["work", "api"]
    )
    return rt


class TestNoteSearchByContent:
    @pytest.mark.asyncio
    async def test_search_title_match(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("Python")
        assert len(results) == 2  # "Python Basics" and "Quick thought on testing" (has python tag)

    @pytest.mark.asyncio
    async def test_search_content_match(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("ACID")
        assert len(results) == 1
        assert results[0].title == "Decision: Use PostgreSQL"

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("sprint")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("nonexistent_xyz")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_tag_match(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("architecture")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_partial_match(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.search_notes("API")
        assert len(results) >= 1


class TestNoteFilterByTags:
    @pytest.mark.asyncio
    async def test_filter_single_tag(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.filter_by_tags(["python"])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filter_multiple_tags(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.filter_by_tags(["work", "python"])
        assert len(results) >= 3  # work: 2, python: 2 (with overlap)

    @pytest.mark.asyncio
    async def test_filter_no_match(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.filter_by_tags(["nonexistent"])
        assert results == []

    @pytest.mark.asyncio
    async def test_filter_case_insensitive(self, runtime_with_notes: NotesRuntime) -> None:
        results = await runtime_with_notes.filter_by_tags(["Python"])
        assert len(results) == 2


class TestNoteGetAllTags:
    @pytest.mark.asyncio
    async def test_get_all_tags(self, runtime_with_notes: NotesRuntime) -> None:
        tags = await runtime_with_notes.get_all_tags()
        assert "python" in tags
        assert "work" in tags
        assert "database" in tags
        assert "testing" in tags

    @pytest.mark.asyncio
    async def test_tags_sorted(self, runtime_with_notes: NotesRuntime) -> None:
        tags = await runtime_with_notes.get_all_tags()
        assert tags == sorted(tags)

    @pytest.mark.asyncio
    async def test_tags_unique(self, runtime_with_notes: NotesRuntime) -> None:
        tags = await runtime_with_notes.get_all_tags()
        assert len(tags) == len(set(tags))
