from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.cache.manager import cache
from app.db.database import db
from app.db.repositories import items, jobs, metadata, state
from app.media.models import MediaItem
from app.metadata.models import Metadata
from app.optimization.queue import JobState
from app.utils.json_utils import read_json


def _already_migrated() -> bool:
    row = db.query_one("SELECT value FROM meta WHERE key='migrated_from_json'")
    return row is not None and row["value"] == "1"


def _mark_migrated() -> None:
    db.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('migrated_from_json','1')")


def maybe_migrate() -> None:
    """One-time import of the legacy JSON files into SQLite.

    Safe to call on every startup: it no-ops once the marker is set or if the
    JSON files are absent (fresh install).
    """
    db.connect()
    if _already_migrated():
        return

    migrated = 0

    # Library index
    index_data = read_json(cache.index_file)
    if isinstance(index_data, list):
        for entry in index_data:
            if not isinstance(entry, dict) or "media_id" not in entry:
                continue
            try:
                items.upsert(MediaItem.model_validate(entry))
                migrated += 1
            except Exception as exc:
                logger.warning("Skipping index entry during migration: {}", exc)

    # Per-item metadata
    metadata_dir = cache.metadata_dir()
    if metadata_dir.is_dir():
        for path in metadata_dir.glob("*.json"):
            raw = read_json(path)
            if not isinstance(raw, dict):
                continue
            try:
                metadata.upsert(Metadata.model_validate(raw))
                migrated += 1
            except Exception as exc:
                logger.warning("Skipping metadata {} during migration: {}", path.name, exc)

    # Playback state
    state_data = read_json(cache.state_file)
    if isinstance(state_data, dict):
        for media_id, entry in state_data.items():
            if isinstance(entry, dict):
                state.update(media_id, **entry)
                migrated += 1

    # Optimization queue
    queue_data = read_json(cache.queue_file)
    if isinstance(queue_data, dict):
        for media_id, entry in queue_data.items():
            if not isinstance(entry, dict):
                continue
            job = JobState(
                media_id=entry.get("media_id", media_id),
                mode=entry.get("mode", "hls"),
                status=entry.get("status", "queued"),
                progress=float(entry.get("progress", 0.0)),
                message=str(entry.get("message", "")),
                error=entry.get("error"),
                created_at=entry.get("created_at") or None,
                finished_at=entry.get("finished_at"),
            )
            jobs.upsert(job.to_dict())
            migrated += 1

    _mark_migrated()
    if migrated:
        logger.info("Migrated {} legacy JSON records into SQLite", migrated)
