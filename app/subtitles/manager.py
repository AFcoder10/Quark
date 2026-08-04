from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.cache.manager import cache
from app.config.settings import settings
from app.metadata.models import Metadata, SubtitleTrackInfo
from app.providers import get_opensubtitles
from app.providers.base import ProviderError

SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa", ".sub"}


class SubtitleManager:
    async def download_external(self, meta: Metadata) -> list[SubtitleTrackInfo]:
        config = settings.data.providers.opensubtitles
        provider = get_opensubtitles()
        entries = await provider.search(
            tmdb_id=meta.tmdb_id,
            imdb_id=meta.imdb_id,
            kind=meta.kind,
            season=meta.season,
            episode=meta.episode,
            languages=config.languages,
        )
        out = cache.subtitles_dir(meta.media_id)
        out.mkdir(parents=True, exist_ok=True)

        present_languages = {track.language for track in meta.subtitles if track.language}
        next_index = max((track.index for track in meta.subtitles if track.index is not None), default=-1) + 1
        new_tracks: list[SubtitleTrackInfo] = []

        for entry in entries[:5]:
            attributes = entry.get("attributes") or {}
            files = attributes.get("files") or []
            if not files:
                continue
            file_id = files[0].get("file_id")
            if not file_id:
                continue
            language = attributes.get("language") or "und"
            forced = bool(attributes.get("forced"))
            try:
                content, file_name = await provider.download(file_id)
            except ProviderError as exc:
                logger.warning("Subtitle download failed: %s", exc)
                continue
            if not content:
                continue
            ext = Path(file_name or "").suffix.lower()
            if ext not in SUBTITLE_EXTENSIONS:
                ext = ".srt"
            target = out / f"{language}-{next_index}{ext}"
            target.write_bytes(content)
            new_tracks.append(
                SubtitleTrackInfo(
                    index=next_index,
                    codec="subrip" if ext in (".srt", ".sub") else ext.lstrip("."),
                    language=language,
                    title=file_name,
                    forced=forced,
                    embedded=False,
                    format=ext.lstrip("."),
                    path=str(target),
                )
            )
            present_languages.add(language)
            next_index += 1

        return new_tracks