from __future__ import annotations

from pathlib import Path

from app.media.models import MediaItem
from app.utils.json_utils import read_json, write_json


class LibraryIndex:
    def __init__(self, file: Path) -> None:
        self.file = file
        self._items: dict[str, MediaItem] = {}

    def load(self) -> None:
        data = read_json(self.file) or []
        self._items = {
            entry["media_id"]: MediaItem.model_validate(entry)
            for entry in data
            if isinstance(entry, dict) and "media_id" in entry
        }

    def save(self) -> None:
        write_json(self.file, [item.model_dump(mode="json") for item in self._items.values()])

    def upsert(self, item: MediaItem) -> None:
        self._items[item.media_id] = item

    def get(self, media_id: str) -> MediaItem | None:
        return self._items.get(media_id)

    def all(self) -> list[MediaItem]:
        return list(self._items.values())

    def by_library(self, library_id: str) -> list[MediaItem]:
        return [item for item in self._items.values() if item.library_id == library_id]

    def remove(self, media_id: str) -> bool:
        return self._items.pop(media_id, None) is not None

    def __len__(self) -> int:
        return len(self._items)