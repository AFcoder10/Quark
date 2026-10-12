from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.config.settings import BASE_DIR
from app.db.repositories import libraries as _repo
from app.utils.json_utils import read_json


class Library(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    path: str
    type: Literal["movie", "show", "music", "photo", "mixed"] = "movie"
    enabled: bool = True

    def resolve_path(self) -> Path:
        p = Path(self.path)
        return p if p.is_absolute() else (BASE_DIR / p).resolve()


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class LibrariesManager:
    """Library folders, stored in the on-device SQLite DB (never committed)."""

    def __init__(self) -> None:
        self._libraries: list[Library] = []

    @property
    def legacy_path(self) -> Path:
        return BASE_DIR / "config" / "libraries.json"

    def load(self) -> list[Library]:
        self._migrate_legacy()
        self._libraries = [Library.model_validate(row) for row in _repo.all()]
        return self._libraries

    def _migrate_legacy(self) -> None:
        """Import any old config/libraries.json into the DB once, then drop it."""
        if _repo.count() > 0:
            return
        raw = read_json(self.legacy_path)
        if not isinstance(raw, list):
            return
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            try:
                _repo.upsert(Library.model_validate(entry).model_dump(mode="json"))
            except Exception:
                continue
        try:
            self.legacy_path.unlink(missing_ok=True)
        except OSError:
            pass

    def all(self) -> list[Library]:
        return list(self._libraries)

    def get(self, library_id: str) -> Library | None:
        return next((lib for lib in self._libraries if lib.id == library_id), None)

    def add(self, name: str, path: str, library_type: str) -> Library:
        lib = Library(id=_new_id(), name=name, path=path, type=library_type)
        self._libraries.append(lib)
        _repo.upsert(lib.model_dump(mode="json"))
        return lib

    def remove(self, library_id: str) -> bool:
        before = len(self._libraries)
        self._libraries = [lib for lib in self._libraries if lib.id != library_id]
        if len(self._libraries) != before:
            _repo.delete(library_id)
            return True
        return False


libraries = LibrariesManager()
