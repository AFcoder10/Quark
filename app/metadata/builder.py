from __future__ import annotations

import shutil
from pathlib import Path

import httpx
from loguru import logger

from app.artwork.manager import ArtworkManager
from app.cache.manager import cache
from app.config.settings import settings
from app.events.bus import event_bus
from app.media.models import MediaItem
from app.media.probe import ProbeResult, probe_media
from app.metadata.models import (
    AudioTrackInfo,
    ChapterInfo,
    FileInfo,
    Metadata,
    SubtitleTrackInfo,
    VideoInfo,
)
from app.providers import get_fanart, get_tmdb
from app.providers.base import ProviderError
from app.subtitles.manager import SubtitleManager
from app.utils.json_utils import write_json
from app.utils.time_utils import utcnow_iso


class MetadataBuilder:
    def __init__(self) -> None:
        self.artwork = ArtworkManager()
        self.subtitles = SubtitleManager()

    async def build(self, item: MediaItem, *, download_subtitles: bool | None = None) -> Metadata:
        event_bus.publish("metadata.started", media_id=item.media_id)

        probe = await probe_media(item.primary)

        meta = self._from_probe(item, probe)
        await self._apply_tmdb(meta)
        await self._apply_artwork(meta)
        await self._apply_external_subtitles(meta, download_subtitles)

        supported, reason = self._direct_play_supported(meta)
        meta.playback.direct_play_supported = supported
        meta.playback.reason = reason
        meta.playback.mode = "direct" if supported else "transcode"

        meta.updated_at = utcnow_iso()
        self.save(meta)

        event_bus.publish("metadata.completed", media_id=meta.media_id, title=meta.title)
        return meta

    def _from_probe(self, item: MediaItem, probe: ProbeResult) -> Metadata:
        video = None
        if probe.video is not None:
            video = VideoInfo(
                codec=probe.video.codec,
                width=probe.video.width,
                height=probe.video.height,
                bitrate=probe.video.bitrate,
                fps=probe.video.fps,
                profile=probe.video.profile,
                level=probe.video.level,
                pixel_format=probe.video.pixel_format,
                color_space=probe.video.color_space,
            )
        audio = [
            AudioTrackInfo(
                index=track.index,
                codec=track.codec,
                language=track.language,
                channels=track.channels,
                sample_rate=track.sample_rate,
                bitrate=track.bitrate,
                title=track.title,
                profile=track.profile,
            )
            for track in probe.audio
        ]
        subtitles = [
            SubtitleTrackInfo(
                index=track.index,
                codec=track.codec,
                language=track.language,
                title=track.title,
                forced=track.forced,
                default=track.default,
                embedded=True,
                format=track.format,
            )
            for track in probe.subtitles
        ]
        chapters = [ChapterInfo(index=chapter.index, time=chapter.time, title=chapter.title) for chapter in probe.chapters]
        files = [
            FileInfo(
                path=file.path,
                size=file.size,
                extension=file.extension,
                container=probe.container,
                duration=probe.duration,
            )
            for file in item.files
        ]
        now = utcnow_iso()
        return Metadata(
            media_id=item.media_id,
            kind=item.kind,
            library_id=item.library_id,
            title=item.title,
            year=item.year,
            season=item.season,
            episode=item.episode,
            series_title=item.series_title,
            files=files,
            primary_file=item.primary_file,
            video=video,
            audio=audio,
            subtitles=subtitles,
            chapters=chapters,
            created_at=now,
            updated_at=now,
        )

    async def _apply_tmdb(self, meta: Metadata) -> None:
        tmdb = get_tmdb()
        try:
            if meta.kind == "movie":
                info = await tmdb.find_movie(meta.title, meta.year)
                if not info or "id" not in info:
                    return
                meta.tmdb_id = info["id"]
                meta.title = info.get("title") or meta.title
                meta.original_title = info.get("original_title")
                meta.overview = info.get("overview")
                meta.rating = info.get("vote_average")
                meta.vote_count = info.get("vote_count")
                meta.popularity = info.get("popularity")
                meta.genres = [genre.get("name") for genre in info.get("genres", []) if genre.get("name")]
                meta.runtime = info.get("runtime")
                meta.tagline = info.get("tagline") or None
                meta.status = info.get("status")
                meta.production_companies = [
                    company.get("name") for company in info.get("production_companies", []) if company.get("name")
                ]
                meta.spoken_languages = [lang.get("name") for lang in info.get("spoken_languages", []) if lang.get("name")]
                release_date = info.get("release_date")
                if release_date:
                    meta.year = int(release_date[:4])
                external = await tmdb.movie_external_ids(info["id"])
                meta.imdb_id = external.get("imdb_id")
                meta.tvdb_id = external.get("tvdb_id")
            else:
                show = await tmdb.find_tv(meta.series_title or meta.title)
                if not show or "id" not in show:
                    return
                meta.tmdb_id = show["id"]
                meta.series_id = show["id"]
                meta.series_title = show.get("name") or meta.series_title
                meta.genres = [genre.get("name") for genre in show.get("genres", []) if genre.get("name")]
                meta.status = show.get("status")
                meta.tagline = show.get("tagline") or None
                meta.networks = [network.get("name") for network in show.get("networks", []) if network.get("name")]
                meta.creators = [
                    creator.get("name") for creator in show.get("created_by", []) if creator.get("name")
                ]
                meta.number_of_seasons = show.get("number_of_seasons")
                meta.number_of_episodes = show.get("number_of_episodes")
                meta.first_air_date = show.get("first_air_date")
                meta.last_air_date = show.get("last_air_date")
                first_air = show.get("first_air_date")
                if first_air:
                    meta.year = int(first_air[:4])
                external = await tmdb.tv_external_ids(show["id"])
                meta.imdb_id = external.get("imdb_id")
                meta.tvdb_id = external.get("tvdb_id")
                if meta.season is not None and meta.episode is not None:
                    episode = await tmdb.episode_details(show["id"], meta.season, meta.episode)
                    meta.title = episode.get("name") or meta.title
                    meta.overview = episode.get("overview")
                    meta.rating = episode.get("vote_average")
                    meta.vote_count = episode.get("vote_count")
                    meta.runtime = episode.get("runtime")
                    meta.air_date = episode.get("air_date") or None
                    if episode.get("still_path"):
                        meta.artwork.still = await self._fetch_still(meta, episode["still_path"])
                    await self._rename_episode_file(meta, episode)
                if not meta.runtime:
                    runtimes = show.get("episode_run_time") or []
                    if runtimes and runtimes[0]:
                        meta.runtime = runtimes[0]
        except ProviderError as exc:
            logger.warning("TMDB match skipped for %s: %s", meta.media_id, exc)

    async def _fetch_still(self, meta: Metadata, still_path: str) -> str | None:
        try:
            from app.artwork.manager import TMDB_IMAGE_BASE

            url = f"{TMDB_IMAGE_BASE}{still_path}"
            out = cache.artwork_dir(meta.media_id)
            out.mkdir(parents=True, exist_ok=True)
            target = out / "still.jpg"
            if target.is_file():
                return str(target)
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200 and response.content:
                    target.write_bytes(response.content)
                    return str(target)
        except Exception as exc:
            logger.warning("Still fetch failed for {}: {}", meta.media_id, exc)
        return None

    async def _apply_artwork(self, meta: Metadata) -> None:
        if not meta.tmdb_id:
            return
        try:
            meta.artwork = await self.artwork.fetch_and_cache(meta)
        except ProviderError as exc:
            logger.warning("Artwork skipped for %s: %s", meta.media_id, exc)

    async def _apply_external_subtitles(self, meta: Metadata, download_subtitles: bool | None) -> None:
        config = settings.data.providers.opensubtitles
        should_download = config.enabled if download_subtitles is None else download_subtitles
        if not should_download or not (meta.tmdb_id or meta.imdb_id):
            return
        try:
            new_tracks = await self.subtitles.download_external(meta)
            if new_tracks:
                meta.subtitles.extend(new_tracks)
        except ProviderError as exc:
            logger.warning("Subtitle download skipped for %s: %s", meta.media_id, exc)

    async def _rename_episode_file(self, meta: Metadata, episode: dict) -> None:
        current_path = Path(meta.primary_file)
        if not current_path.is_file():
            return

        ep_name = episode.get("name", "").strip()
        if not ep_name:
            return

        safe_name = "".join(c if c.isalnum() or c in " -._()" else "" for c in ep_name)
        safe_name = safe_name.strip(" .-_")
        if not safe_name:
            return

        season = meta.season or 0
        episode_num = meta.episode or 0
        ext = current_path.suffix
        new_name = f"{season:02d}x{episode_num:02d} - {safe_name}{ext}"
        new_path = current_path.parent / new_name

        if new_path.exists() and new_path != current_path:
            return

        if new_path == current_path:
            return

        try:
            shutil.move(str(current_path), str(new_path))
        except OSError as exc:
            logger.warning("Failed to rename {} -> {}: {}", current_path.name, new_name, exc)
            return

        meta.primary_file = str(new_path)
        if meta.files:
            meta.files[0].path = str(new_path)
        event_bus.publish("metadata.renamed", media_id=meta.media_id, old=current_path.name, new=new_name)

    DIRECT_PLAY_AUDIO_CODECS = {"aac", "mp3", "opus", "vorbis", "flac", "eac3", "ac3"}

    def _direct_play_supported(self, meta: Metadata) -> tuple[bool, str]:
        video = meta.video
        if video is None or not video.codec:
            return False, "no video stream"
        if video.codec.lower() not in settings.data.streaming.direct_play_codecs:
            return False, f"codec {video.codec} not supported for direct play"
        ext = Path(meta.primary_file).suffix.lower().lstrip(".")
        if ext not in settings.data.streaming.direct_play_containers:
            return False, f"container {ext} not supported for direct play"

        if meta.audio:
            primary_audio = meta.audio[0]
            audio_codec = (primary_audio.codec or "").lower()
            if audio_codec and audio_codec not in self.DIRECT_PLAY_AUDIO_CODECS:
                return False, f"audio codec {audio_codec} requires transcode for browser audio playback"

        return True, "direct play supported"

    def load(self, media_id: str) -> Metadata | None:
        from app.utils.json_utils import read_json

        raw = read_json(cache.metadata_file(media_id))
        if not raw:
            return None
        return Metadata.model_validate(raw)

    def save(self, meta: Metadata) -> None:
        write_json(cache.metadata_file(meta.media_id), meta.model_dump(mode="json"))