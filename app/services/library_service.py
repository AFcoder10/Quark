from __future__ import annotations

import asyncio

from loguru import logger

from app.cache.manager import cache
from app.config.libraries import Library, libraries
from app.metadata.builder import MetadataBuilder
from app.metadata.models import Metadata
from app.scanner.index import LibraryIndex
from app.scanner.scanner import LibraryScanner
from app.subtitles.manager import SubtitleManager


class LibraryService:
    def __init__(self, scanner: LibraryScanner, index: LibraryIndex) -> None:
        self.scanner = scanner
        self.index = index
        self.builder = MetadataBuilder()
        self.subtitles = SubtitleManager()

    def list_libraries(self) -> list[Library]:
        return libraries.all()

    def add_library(self, name: str, path: str, library_type: str) -> Library:
        return libraries.add(name=name, path=path, library_type=library_type)

    def remove_library(self, library_id: str) -> bool:
        return libraries.remove(library_id)

    def items(self, *, library_id: str | None = None, kind: str | None = None, search: str | None = None) -> list:
        items = self.index.all()
        if library_id:
            items = [item for item in items if item.library_id == library_id]
        if kind in ("movie", "episode"):
            items = [item for item in items if item.kind == kind]
        if search:
            query = search.lower()
            items = [
                item
                for item in items
                if query in item.title.lower()
                or (item.series_title and query in item.series_title.lower())
                or query in item.primary_file.lower()
            ]
        return items

    def item(self, media_id: str):
        return self.index.get(media_id)

    def remove_item(self, media_id: str) -> bool:
        removed = self.index.remove(media_id)
        if removed:
            self.index.save()
            cache.clear_media(media_id)
        return removed

    async def metadata(self, media_id: str) -> Metadata | None:
        return self.builder.load(media_id)

    def refresh(self, media_id: str) -> bool:
        item = self.index.get(media_id)
        if item is None:
            return False
        asyncio.create_task(self._refresh_task(item.media_id))
        return True

    async def _refresh_task(self, media_id: str) -> None:
        item = self.index.get(media_id)
        if item is None:
            return
        try:
            await self.builder.build(item, download_subtitles=True)
        except Exception as exc:
            logger.exception("Metadata refresh failed for %s", media_id)
            from app.events.bus import event_bus

            event_bus.publish("metadata.failed", media_id=media_id, error=str(exc))

    def download_subtitles(self, media_id: str) -> bool:
        meta = self.builder.load(media_id)
        if meta is None:
            return False
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._download_subtitles_task(media_id))
        except RuntimeError:
            asyncio.run(self._download_subtitles_task(media_id))
        return True

    async def _download_subtitles_task(self, media_id: str) -> None:
        from app.events.bus import event_bus

        meta = self.builder.load(media_id)
        if meta is None:
            return
        try:
            new_tracks = await self.subtitles.download_external(meta)
            if new_tracks:
                meta.subtitles.extend(new_tracks)
                self.builder.save(meta)
            event_bus.publish("subtitles.downloaded", media_id=media_id, count=len(new_tracks))
        except Exception as exc:
            logger.exception("Subtitle download failed for %s", media_id)
            event_bus.publish("subtitles.failed", media_id=media_id, error=str(exc))