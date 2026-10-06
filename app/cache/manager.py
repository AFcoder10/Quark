from __future__ import annotations

import shutil
from pathlib import Path

from app.config.settings import BASE_DIR


class CacheManager:
    """Central access point for all runtime cache paths.

    Layout (all under ``<repo>/cache/``)::

        cache/
        ├── index.json            # library index
        ├── state.json            # playback state
        ├── queue.json            # optimization queue
        ├── metadata/<id>.json    # per-item metadata
        ├── artwork/<id>/         # cached artwork
        ├── subtitles/<id>/       # downloaded / extracted subtitles
        ├── optimized/<id>/       # pre-encoded HLS output
        └── live/<id>/            # live transcode output
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else BASE_DIR / "cache"

    # -- top level ---------------------------------------------------------
    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def index_file(self) -> Path:
        return self.root / "index.json"

    @property
    def state_file(self) -> Path:
        return self.root / "state.json"

    @property
    def queue_file(self) -> Path:
        return self.root / "queue.json"

    # -- per media ---------------------------------------------------------
    def metadata_dir(self) -> Path:
        return self.root / "metadata"

    def metadata_file(self, media_id: str) -> Path:
        return self.metadata_dir() / f"{media_id}.json"

    def artwork_dir(self, media_id: str) -> Path:
        return self.root / "artwork" / media_id

    def subtitles_dir(self, media_id: str) -> Path:
        return self.root / "subtitles" / media_id

    def optimized_dir(self, media_id: str) -> Path:
        return self.root / "optimized" / media_id

    def live_dir(self, media_id: str) -> Path:
        return self.root / "live" / media_id

    # -- cleanup -----------------------------------------------------------
    def clear_optimized(self, media_id: str) -> None:
        shutil.rmtree(self.optimized_dir(media_id), ignore_errors=True)
        shutil.rmtree(self.live_dir(media_id), ignore_errors=True)

    def clear_media(self, media_id: str) -> None:
        from app.db.repositories import metadata as _metadata_repo

        self.metadata_file(media_id).unlink(missing_ok=True)
        _metadata_repo.delete(media_id)
        shutil.rmtree(self.artwork_dir(media_id), ignore_errors=True)
        shutil.rmtree(self.subtitles_dir(media_id), ignore_errors=True)
        self.clear_optimized(media_id)


cache = CacheManager()
