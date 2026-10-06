from __future__ import annotations

import threading

from app.db.database import db
from app.media.models import MediaItem
from app.metadata.models import Metadata
from app.utils.json_utils import dumps, loads
from app.utils.time_utils import utcnow_iso


class ItemRepository:
    """Persistent store for the library index (MediaItem records)."""

    def __init__(self) -> None:
        self._cache: dict[str, MediaItem] | None = None
        self._lock = threading.RLock()

    def load(self) -> None:
        with self._lock:
            rows = db.query("SELECT data FROM items")
            loaded = [MediaItem.model_validate(loads(row["data"])) for row in rows]
            self._cache = {item.media_id: item for item in loaded}

    def _items(self) -> dict[str, MediaItem]:
        if self._cache is None:
            self.load()
        assert self._cache is not None
        return self._cache

    def upsert(self, item: MediaItem) -> None:
        with self._lock:
            self._items()[item.media_id] = item
            db.execute(
                """
                INSERT INTO items(media_id, kind, library_id, title, series_title,
                                  season, episode, year, display_title, data)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(media_id) DO UPDATE SET
                    kind=excluded.kind, library_id=excluded.library_id,
                    title=excluded.title, series_title=excluded.series_title,
                    season=excluded.season, episode=excluded.episode,
                    year=excluded.year, display_title=excluded.display_title,
                    data=excluded.data
                """,
                (
                    item.media_id,
                    item.kind.value if hasattr(item.kind, "value") else str(item.kind),
                    item.library_id,
                    item.title,
                    item.series_title,
                    item.season,
                    item.episode,
                    item.year,
                    item.display_title,
                    dumps(item.model_dump(mode="json")),
                ),
            )

    def get(self, media_id: str) -> MediaItem | None:
        with self._lock:
            return self._items().get(media_id)

    def all(self) -> list[MediaItem]:
        with self._lock:
            return list(self._items().values())

    def by_library(self, library_id: str) -> list[MediaItem]:
        with self._lock:
            return [item for item in self._items().values() if item.library_id == library_id]

    def by_series(self, series_title: str) -> list[MediaItem]:
        with self._lock:
            return [
                item
                for item in self._items().values()
                if item.kind == "episode" and (item.series_title or item.title) == series_title
            ]

    def remove(self, media_id: str) -> bool:
        with self._lock:
            existed = self._items().pop(media_id, None) is not None
            if existed:
                db.execute("DELETE FROM items WHERE media_id=?", (media_id,))
            return existed

    def count(self) -> int:
        with self._lock:
            return len(self._items())

    def __len__(self) -> int:
        return self.count()


class MetadataRepository:
    def upsert(self, meta: Metadata) -> None:
        db.execute(
            """
            INSERT INTO metadata(media_id, kind, library_id, title, updated_at, data)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(media_id) DO UPDATE SET
                kind=excluded.kind, library_id=excluded.library_id,
                title=excluded.title, updated_at=excluded.updated_at,
                data=excluded.data
            """,
            (
                meta.media_id,
                meta.kind.value if hasattr(meta.kind, "value") else str(meta.kind),
                meta.library_id,
                meta.title,
                meta.updated_at or utcnow_iso(),
                dumps(meta.model_dump(mode="json")),
            ),
        )

    def get(self, media_id: str) -> Metadata | None:
        row = db.query_one("SELECT data FROM metadata WHERE media_id=?", (media_id,))
        if row is None:
            return None
        return Metadata.model_validate(loads(row["data"]))

    def delete(self, media_id: str) -> None:
        db.execute("DELETE FROM metadata WHERE media_id=?", (media_id,))

    def all(self) -> list[Metadata]:
        rows = db.query("SELECT data FROM metadata")
        return [Metadata.model_validate(loads(row["data"])) for row in rows]


class StateRepository:
    def get(self, media_id: str) -> dict:
        row = db.query_one("SELECT * FROM playback_state WHERE media_id=?", (media_id,))
        if row is None:
            return {"position": 0.0, "duration": 0.0, "watched": False, "last_played_at": None}
        return {
            "position": row["position"] or 0.0,
            "duration": row["duration"] or 0.0,
            "watched": bool(row["watched"]),
            "last_played_at": row["last_played_at"],
        }

    def update(self, media_id: str, **values) -> dict:
        data = self.get(media_id)
        for key, value in values.items():
            if value is not None:
                data[key] = value
        db.execute(
            """
            INSERT INTO playback_state(media_id, position, duration, watched, last_played_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(media_id) DO UPDATE SET
                position=excluded.position, duration=excluded.duration,
                watched=excluded.watched, last_played_at=excluded.last_played_at
            """,
            (
                media_id,
                float(data.get("position") or 0.0),
                float(data.get("duration") or 0.0),
                1 if data.get("watched") else 0,
                data.get("last_played_at"),
            ),
        )
        return self.get(media_id)

    def all(self) -> dict[str, dict]:
        rows = db.query("SELECT * FROM playback_state")
        return {
            row["media_id"]: {
                "position": row["position"] or 0.0,
                "duration": row["duration"] or 0.0,
                "watched": bool(row["watched"]),
                "last_played_at": row["last_played_at"],
            }
            for row in rows
        }


class JobRepository:
    def upsert(self, job: dict) -> None:
        db.execute(
            """
            INSERT INTO optimization_jobs(media_id, mode, status, progress, message, error, created_at, finished_at)
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(media_id) DO UPDATE SET
                mode=excluded.mode, status=excluded.status, progress=excluded.progress,
                message=excluded.message, error=excluded.error,
                created_at=excluded.created_at, finished_at=excluded.finished_at
            """,
            (
                job["media_id"],
                job.get("mode", "hls"),
                job.get("status", "queued"),
                float(job.get("progress", 0.0)),
                job.get("message", ""),
                job.get("error"),
                job.get("created_at"),
                job.get("finished_at"),
            ),
        )

    def delete(self, media_id: str) -> None:
        db.execute("DELETE FROM optimization_jobs WHERE media_id=?", (media_id,))

    def all(self) -> list[dict]:
        rows = db.query("SELECT * FROM optimization_jobs")
        return [dict(row) for row in rows]


# Module-level singletons
items = ItemRepository()
metadata = MetadataRepository()
state = StateRepository()
jobs = JobRepository()


class LibraryRepository:
    def all(self) -> list[dict]:
        rows = db.query("SELECT * FROM libraries ORDER BY name")
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "path": row["path"],
                "type": row["type"],
                "enabled": bool(row["enabled"]),
            }
            for row in rows
        ]

    def upsert(self, library: dict) -> None:
        db.execute(
            """
            INSERT INTO libraries(id, name, path, type, enabled)
            VALUES(?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, path=excluded.path,
                type=excluded.type, enabled=excluded.enabled
            """,
            (
                library["id"],
                library["name"],
                library["path"],
                library.get("type", "movie"),
                1 if library.get("enabled", True) else 0,
            ),
        )

    def delete(self, library_id: str) -> bool:
        cur = db.execute("DELETE FROM libraries WHERE id=?", (library_id,))
        return cur.rowcount > 0

    def count(self) -> int:
        row = db.query_one("SELECT COUNT(*) AS n FROM libraries")
        return int(row["n"]) if row else 0


libraries = LibraryRepository()

