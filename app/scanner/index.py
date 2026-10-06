from __future__ import annotations

from pathlib import Path

from app.db.repositories import items as _items
from app.media.models import MediaItem


class LibraryIndex:
    """Facade over the SQLite item repository.

    Kept with the same method surface as the original JSON-backed index so the
    rest of the codebase (and the API layer) does not need to change.
    """

    def __init__(self, file: Path | None = None) -> None:
        # `file` is retained for backwards compatibility; persistence now lives
        # in SQLite (see app/db).
        self.file = file
        self._items = _items

    def load(self) -> None:
        self._items.load()

    def save(self) -> None:
        # Writes are persisted immediately by the repository.
        return None

    def upsert(self, item: MediaItem) -> None:
        self._items.upsert(item)

    def get(self, media_id: str) -> MediaItem | None:
        return self._items.get(media_id)

    def all(self) -> list[MediaItem]:
        return self._items.all()

    def by_library(self, library_id: str) -> list[MediaItem]:
        return self._items.by_library(library_id)

    def by_series(self, series_title: str) -> list[MediaItem]:
        return self._items.by_series(series_title)

    def remove(self, media_id: str) -> bool:
        return self._items.remove(media_id)

    def __len__(self) -> int:
        return len(self._items)
