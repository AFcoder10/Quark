from __future__ import annotations

from pathlib import Path

from app.db.repositories import state as _state
from app.utils.time_utils import utcnow_iso


class PlaybackState:
    def __init__(
        self,
        position: float = 0.0,
        duration: float = 0.0,
        watched: bool = False,
        last_played_at: str | None = None,
    ) -> None:
        self.position = position
        self.duration = duration
        self.watched = watched
        self.last_played_at = last_played_at

    def model_dump(self) -> dict:
        return self.__dict__.copy()


class StateStore:
    """Facade over the SQLite playback-state repository."""

    def __init__(self, path: Path | None = None) -> None:
        # `path` retained for backwards compatibility; storage is now SQLite.
        self.path = path

    def load(self) -> None:
        return None

    def save(self) -> None:
        return None

    def get(self, media_id: str) -> PlaybackState:
        return PlaybackState(**_state.get(media_id))

    def update(self, media_id: str, **values) -> PlaybackState:
        return PlaybackState(**_state.update(media_id, **values))

    def mark_watched(self, media_id: str, watched: bool = True) -> PlaybackState:
        return self.update(media_id, watched=watched, last_played_at=utcnow_iso() if watched else None)

    def progress(self, media_id: str, position: float, duration: float) -> PlaybackState:
        watched = duration > 0 and position / duration >= 0.9
        return self.update(
            media_id,
            position=position,
            duration=duration,
            watched=watched,
            last_played_at=utcnow_iso(),
        )

    def all_states(self) -> dict[str, dict]:
        return _state.all()
