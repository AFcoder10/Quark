from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from app.config.libraries import Library
from app.events.bus import event_bus
from app.media.detection import build_movie_items, build_tvshow_items, is_media_file
from app.metadata.builder import MetadataBuilder
from app.scanner.index import LibraryIndex


@dataclass
class ScanResult:
    library_id: str
    added: int = 0
    removed: int = 0


class LibraryScanner:
    def __init__(self, index: LibraryIndex) -> None:
        self.index = index
        self.builder = MetadataBuilder()

    async def scan_library(self, library: Library, *, build_metadata: bool = True) -> ScanResult:
        root = library.resolve_path()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Library path does not exist: {root}")

        logger.info("Scanning library '{}' at {}", library.name, root)
        event_bus.publish("scan.started", library_id=library.id, library_name=library.name)

        if library.type == "show":
            items = await asyncio.to_thread(build_tvshow_items, library, root)
        else:
            all_files = await asyncio.to_thread(self._collect_files, root)
            video_files = [f for f in all_files if is_media_file(f)]
            items = await asyncio.to_thread(build_movie_items, library, video_files)

        previous = self.index.by_library(library.id)
        added = 0
        for item in items:
            existing = self.index.get(item.media_id)
            if existing is None:
                added += 1
            self.index.upsert(item)

        previous_ids = {item.media_id for item in previous}
        current_ids = {item.media_id for item in items}
        stale_ids = previous_ids - current_ids
        removed = len(stale_ids)
        for media_id in stale_ids:
            self.index.remove(media_id)

        self.index.save()

        if build_metadata:
            for idx, item in enumerate(items):
                cached = self.builder.load(item.media_id)
                if cached is not None and cached.has_tmdb():
                    continue
                try:
                    await self.builder.build(item, download_subtitles=False)
                except Exception as exc:
                    logger.warning("Metadata build failed for {}: {}", item.display_title, exc)
                if idx % 4 == 3:
                    await asyncio.sleep(0.1)

        event_bus.publish(
            "scan.completed",
            library_id=library.id,
            added=added,
            removed=removed,
        )

        return ScanResult(library_id=library.id, added=added, removed=removed)

    @staticmethod
    def _collect_files(root: Path) -> list[Path]:
        found: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if name.startswith("."):
                    continue
                found.append(Path(dirpath) / name)
        return found