from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.config.settings import BASE_DIR
from app.utils.json_utils import read_json, write_json


class Library(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    path: str
    type: Literal["movie", "show"] = "movie"
    enabled: bool = True

    def resolve_path(self) -> Path:
        p = Path(self.path)
        return p if p.is_absolute() else (BASE_DIR / p).resolve()


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class LibrariesManager:
    def __init__(self) -> None:
        self._libraries: list[Library] = []

    @property
    def path(self) -> Path:
        return BASE_DIR / "config" / "libraries.json"

    def load(self) -> list[Library]:
        raw = read_json(self.path)
        self._libraries = [Library.model_validate(item) for item in raw] if raw else []
        return self._libraries

    def save(self) -> None:
        write_json(self.path, [lib.model_dump(mode="json") for lib in self._libraries])

    def all(self) -> list[Library]:
        return list(self._libraries)

    def get(self, library_id: str) -> Library | None:
        return next((lib for lib in self._libraries if lib.id == library_id), None)

    def add(self, name: str, path: str, library_type: str) -> Library:
        lib = Library(id=_new_id(), name=name, path=path, type=library_type)
        self._libraries.append(lib)
        self.save()
        return lib

    def remove(self, library_id: str) -> bool:
        before = len(self._libraries)
        self._libraries = [lib for lib in self._libraries if lib.id != library_id]
        if len(self._libraries) != before:
            self.save()
            return True
        return False


libraries = LibrariesManager()