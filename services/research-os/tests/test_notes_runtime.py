"""Tests for notes runtime."""

import pytest

from sona_research.domain.personal_models import NoteType
from sona_research.infrastructure.notes.runtime import NotesRuntime


@pytest.fixture
def runtime() -> NotesRuntime:
    return NotesRuntime()


class TestNotesCreate:
    @pytest.mark.asyncio
    async def test_create_note(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Test", "Content")
        assert note.title == "Test"
        assert note.content == "Content"
        assert note.note_id.startswith("note-")

    @pytest.mark.asyncio
    async def test_create_with_type(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Meeting", "Notes", NoteType.MEETING)
        assert note.note_type == NoteType.MEETING

    @pytest.mark.asyncio
    async def test_create_with_tags(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Tagged", "Content", tags=["work", "urgent"])
        assert note.tags == ["work", "urgent"]

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("T", "C")
        assert note.created_at != ""
        assert note.updated_at != ""

    @pytest.mark.asyncio
    async def test_create_emits_event(self, runtime: NotesRuntime) -> None:
        await runtime.create_note("Event Test", "Body")
        assert len(runtime.events) == 1
        assert runtime.events[0].title == "Event Test"

    @pytest.mark.asyncio
    async def test_unique_ids(self, runtime: NotesRuntime) -> None:
        n1 = await runtime.create_note("A", "a")
        n2 = await runtime.create_note("B", "b")
        assert n1.note_id != n2.note_id


class TestNotesRetrieve:
    @pytest.mark.asyncio
    async def test_get_note(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Test", "Content")
        retrieved = await runtime.get_note(note.note_id)
        assert retrieved is not None
        assert retrieved.title == "Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, runtime: NotesRuntime) -> None:
        result = await runtime.get_note("nonexistent")
        assert result is None


class TestNotesUpdate:
    @pytest.mark.asyncio
    async def test_update_title(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Old", "Content")
        updated = await runtime.update_note(note.note_id, title="New")
        assert updated is not None
        assert updated.title == "New"
        assert updated.content == "Content"

    @pytest.mark.asyncio
    async def test_update_content(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Title", "Old content")
        updated = await runtime.update_note(note.note_id, content="New content")
        assert updated is not None
        assert updated.content == "New content"

    @pytest.mark.asyncio
    async def test_update_tags(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("T", "C", tags=["old"])
        updated = await runtime.update_note(note.note_id, tags=["new"])
        assert updated is not None
        assert updated.tags == ["new"]

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, runtime: NotesRuntime) -> None:
        result = await runtime.update_note("nonexistent", title="X")
        assert result is None


class TestNotesDelete:
    @pytest.mark.asyncio
    async def test_delete_note(self, runtime: NotesRuntime) -> None:
        note = await runtime.create_note("Del", "Delete me")
        assert await runtime.delete_note(note.note_id) is True
        assert await runtime.get_note(note.note_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, runtime: NotesRuntime) -> None:
        assert await runtime.delete_note("nope") is False


class TestNotesList:
    @pytest.mark.asyncio
    async def test_list_all(self, runtime: NotesRuntime) -> None:
        await runtime.create_note("A", "a")
        await runtime.create_note("B", "b")
        notes = await runtime.list_notes()
        assert len(notes) == 2

    @pytest.mark.asyncio
    async def test_list_by_type(self, runtime: NotesRuntime) -> None:
        await runtime.create_note("Q", "q", NoteType.QUICK)
        await runtime.create_note("M", "m", NoteType.MEETING)
        await runtime.create_note("Q2", "q2", NoteType.QUICK)
        notes = await runtime.list_notes(NoteType.QUICK)
        assert len(notes) == 2

    @pytest.mark.asyncio
    async def test_count(self, runtime: NotesRuntime) -> None:
        await runtime.create_note("A", "a")
        await runtime.create_note("B", "b")
        assert await runtime.count() == 2
