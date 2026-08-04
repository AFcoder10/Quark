from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.utils.json_utils import read_json, write_json


@dataclass
class PlaybackState:
    position: float = 0.0
    duration: float = 0.0
    watched: bool = False
    last_played_at: str | None = None


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._data: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        with self._lock:
            raw = read_json(self.path)
            if isinstance(raw, dict):
                self._data = raw
            else:
                self._data = {}

    def save(self) -> None:
        with self._lock:
            write_json(self.path, self._data)

    def get(self, media_id: str) -> PlaybackState:
        with self._lock:
            data = self._data.get(media_id, {})
        return PlaybackState(**{**PlaybackState().__dict__, **data})

    def update(self, media_id: str, **values) -> PlaybackState:
        with self._lock:
            entry = self._data.setdefault(media_id, {})
            for key, value in values.items():
                if value is not None:
                    entry[key] = value
            state = PlaybackState(**{**PlaybackState().__dict__, **entry})
        self.save()
        return state

    def mark_watched(self, media_id: str, watched: bool = True) -> PlaybackState:
        from app.utils.time_utils import utcnow_iso

        state = self.update(media_id, watched=watched, last_played_at=utcnow_iso() if watched else None)
        return state

    def progress(self, media_id: str, position: float, duration: float) -> PlaybackState:
        from app.utils.time_utils import utcnow_iso

        watched = duration > 0 and position / duration >= 0.9
        return self.update(media_id, position=position, duration=duration, watched=watched, last_played_at=utcnow_iso())

    def all_states(self) -> dict[str, dict]:
        with self._lock:
            return {k: dict(v) for k, v in self._data.items()}
