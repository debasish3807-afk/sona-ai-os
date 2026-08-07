"""Notes runtime for personal knowledge management.

Provides CRUD operations for notes with tag-based filtering
and full-text search capabilities.
"""

from datetime import UTC, datetime

import structlog

from sona_research.domain.events import NoteCreatedEvent
from sona_research.domain.personal_models import Note, NoteType

logger = structlog.get_logger()


class NotesRuntime:
    """Runtime for managing personal notes.

    Supports creation, retrieval, update, deletion, tag-based filtering,
    and full-text search across note content.
    """

    def __init__(self) -> None:
        """Initialize the notes runtime."""
        self._notes: dict[str, Note] = {}
        self._events: list[NoteCreatedEvent] = []
        self._next_id: int = 1

    @property
    def events(self) -> list[NoteCreatedEvent]:
        """Access emitted events."""
        return self._events

    def _generate_id(self) -> str:
        """Generate a unique note ID."""
        note_id = f"note-{self._next_id:04d}"
        self._next_id += 1
        return note_id

    async def create_note(
        self,
        title: str,
        content: str,
        note_type: NoteType = NoteType.QUICK,
        tags: list[str] | None = None,
    ) -> Note:
        """Create a new note.

        Args:
            title: Note title.
            content: Note content.
            note_type: Type of note.
            tags: Optional list of tags.

        Returns:
            The created Note instance.
        """
        now = datetime.now(UTC).isoformat()
        note = Note(
            note_id=self._generate_id(),
            title=title,
            content=content,
            note_type=note_type,
            tags=tags or [],
            created_at=now,
            updated_at=now,
        )
        self._notes[note.note_id] = note

        event = NoteCreatedEvent(note_id=note.note_id, title=title)
        self._events.append(event)

        logger.info("notes.created", note_id=note.note_id, title=title)
        return note

    async def get_note(self, note_id: str) -> Note | None:
        """Get a note by ID.

        Args:
            note_id: The note identifier.

        Returns:
            The Note if found, None otherwise.
        """
        return self._notes.get(note_id)

    async def update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> Note | None:
        """Update an existing note.

        Args:
            note_id: The note identifier.
            title: New title (None to keep current).
            content: New content (None to keep current).
            tags: New tags (None to keep current).

        Returns:
            The updated Note if found, None otherwise.
        """
        existing = self._notes.get(note_id)
        if existing is None:
            return None

        now = datetime.now(UTC).isoformat()
        updated = Note(
            note_id=existing.note_id,
            title=title if title is not None else existing.title,
            content=content if content is not None else existing.content,
            note_type=existing.note_type,
            tags=tags if tags is not None else existing.tags,
            created_at=existing.created_at,
            updated_at=now,
        )
        self._notes[note_id] = updated
        logger.info("notes.updated", note_id=note_id)
        return updated

    async def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID.

        Args:
            note_id: The note identifier.

        Returns:
            True if the note was found and deleted.
        """
        if note_id in self._notes:
            del self._notes[note_id]
            logger.info("notes.deleted", note_id=note_id)
            return True
        return False

    async def list_notes(self, note_type: NoteType | None = None) -> list[Note]:
        """List all notes, optionally filtered by type.

        Args:
            note_type: Optional type filter.

        Returns:
            List of matching notes.
        """
        notes = list(self._notes.values())
        if note_type is not None:
            notes = [n for n in notes if n.note_type == note_type]
        return notes

    async def search_notes(self, query: str) -> list[Note]:
        """Full-text search across notes.

        Searches in title, content, and tags.

        Args:
            query: Search query string.

        Returns:
            List of matching notes.
        """
        query_lower = query.lower()
        results: list[Note] = []

        for note in self._notes.values():
            if (
                query_lower in note.title.lower()
                or query_lower in note.content.lower()
                or any(query_lower in tag.lower() for tag in note.tags)
            ):
                results.append(note)

        return results

    async def filter_by_tags(self, tags: list[str]) -> list[Note]:
        """Filter notes by tags (any match).

        Args:
            tags: List of tags to filter by.

        Returns:
            Notes that have at least one of the specified tags.
        """
        tag_set = {t.lower() for t in tags}
        results: list[Note] = []

        for note in self._notes.values():
            note_tags = {t.lower() for t in note.tags}
            if note_tags & tag_set:
                results.append(note)

        return results

    async def get_all_tags(self) -> list[str]:
        """Get all unique tags across all notes.

        Returns:
            Sorted list of unique tags.
        """
        tags: set[str] = set()
        for note in self._notes.values():
            tags.update(note.tags)
        return sorted(tags)

    async def count(self) -> int:
        """Get total number of notes.

        Returns:
            Count of notes in the store.
        """
        return len(self._notes)
