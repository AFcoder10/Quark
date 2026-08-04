from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Callable

from app.cache.manager import cache
from app.config.settings import settings
from app.metadata.models import (
    AudioPlaylistInfo,
    Metadata,
    RenditionInfo,
    SubtitlePlaylistInfo,
)
from app.streaming.hls import build_master_playlist
from app.system.commands import FFMPEG, require_binary
from app.transcoding.ffmpeg import FFmpegProcessError, FFmpegRunner
from app.utils.json_utils import write_json
from app.utils.time_utils import utcnow_iso

RENDITION_HEIGHTS = {
    "2160p": 2160,
    "1440p": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
    "240p": 240,
    "144p": 144,
}

ESTIMATED_VIDEO_BITRATES = {
    2160: 25000,
    1440: 12000,
    1080: 6000,
    720: 3000,
    480: 1500,
    360: 800,
    240: 400,
    144: 250,
}

AUDIO_FALLBACK_BITRATE = 128


class OptimizationError(Exception):
    pass


class HLSBuilder:
    def __init__(self, on_progress: Callable[[float, str], None] | None = None) -> None:
        self.on_progress = on_progress

    def _progress(self, fraction: float, message: str) -> None:
        if self.on_progress is not None:
            self.on_progress(fraction, message)

    async def build(self, meta: Metadata) -> Metadata:
        require_binary(FFMPEG)
        media_id = meta.media_id
        primary = Path(meta.primary_file)
        if not primary.exists():
            raise OptimizationError(f"Media file not found: {primary}")

        out = cache.optimized_dir(media_id)
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True, exist_ok=True)

        src_w = meta.video.width if meta.video else None
        src_h = meta.video.height if meta.video else None
        if not src_w or not src_h:
            src_w, src_h = 1920, 1080

        config = settings.data.optimization
        heights = [RENDITION_HEIGHTS[name] for name in config.renditions if name in RENDITION_HEIGHTS]
        applicable = [height for height in heights if height <= src_h]
        if not applicable:
            applicable = [min(heights)]

        total_steps = len(applicable) + len(meta.audio) + len(meta.subtitles) + 1
        step = 0
        audio_bitrate_total = sum((track.bitrate or 0) // 1000 for track in meta.audio) or len(meta.audio) * AUDIO_FALLBACK_BITRATE

        renditions: list[RenditionInfo] = []
        for height in applicable:
            step += 1
            self._progress(step / total_steps, f"Rendering {height}p")
            name = f"{height}p"
            rendition_dir = out / name
            rendition_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                require_binary(FFMPEG),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(primary),
                "-map",
                "0:v:0",
            ]
            for position, track in enumerate(meta.audio):
                cmd += ["-map", f"0:a:{position}"]
            cmd += [
                "-vf",
                f"scale=-2:{height}",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                config.video_codec,
                "-preset",
                config.preset,
                "-crf",
                str(config.crf),
                "-sc_threshold",
                "0",
                "-force_key_frames",
                f"expr:gte(t,n_forced*{config.segment_seconds})",
            ]
            for position, track in enumerate(meta.audio):
                if (track.codec or "").lower() in config.audio_copy_codecs:
                    cmd += [f"-c:a:{position}", "copy"]
                else:
                    cmd += [f"-c:a:{position}", "aac", f"-b:a:{position}", "192k"]
            cmd += [
                "-hls_time",
                str(config.segment_seconds),
                "-hls_playlist_type",
                "vod",
                "-hls_segment_filename",
                str(rendition_dir / "seg_%05d.ts"),
                str(rendition_dir / "index.m3u8"),
            ]
            try:
                await FFmpegRunner(cmd, log_tag=f"opt-{name}").run()
            except FFmpegProcessError as exc:
                raise OptimizationError(f"{name} rendition failed: {exc}") from exc

            width = max(2, int(round(src_w * height / src_h / 2) * 2))
            bitrate = ESTIMATED_VIDEO_BITRATES.get(height, 3000) + max(audio_bitrate_total, len(meta.audio) * AUDIO_FALLBACK_BITRATE)
            renditions.append(
                RenditionInfo(
                    name=name,
                    height=height,
                    width=width,
                    bitrate=bitrate,
                    playlist=f"{name}/index.m3u8",
                )
            )

        audio_playlists: list[AudioPlaylistInfo] = []
        for position, track in enumerate(meta.audio):
            step += 1
            self._progress(step / total_steps, f"Preparing audio track {position + 1}")
            audio_dir = out / "audio" / f"a{position}"
            audio_dir.mkdir(parents=True, exist_ok=True)
            copyable = (track.codec or "").lower() in config.audio_copy_codecs
            codec_args = ["-c:a:0", "copy"] if copyable else ["-c:a:0", "aac", "-b:a:0", "192k"]
            cmd = [
                require_binary(FFMPEG),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(primary),
                "-map",
                f"0:a:{position}",
                *codec_args,
                "-hls_time",
                str(config.segment_seconds),
                "-hls_playlist_type",
                "vod",
                "-hls_segment_filename",
                str(audio_dir / "seg_%05d.ts"),
                str(audio_dir / "index.m3u8"),
            ]
            try:
                await FFmpegRunner(cmd, log_tag=f"opt-audio-{position}").run()
            except FFmpegProcessError:
                continue
            audio_playlists.append(
                AudioPlaylistInfo(
                    index=position,
                    language=track.language or "und",
                    title=track.title or f"Audio {position + 1}",
                    playlist=f"audio/a{position}/index.m3u8",
                    codec=track.codec or "aac",
                )
            )

        subtitle_playlists: list[SubtitlePlaylistInfo] = []
        for position, track in enumerate(meta.subtitles):
            step += 1
            self._progress(step / total_steps, f"Preparing subtitle {position + 1}")
            subs_dir = out / "subtitles"
            subs_dir.mkdir(parents=True, exist_ok=True)
            vtt_path = subs_dir / f"s{position}.vtt"
            if track.embedded:
                cmd = [
                    require_binary(FFMPEG),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(primary),
                    "-map",
                    f"0:{track.index}",
                    "-c:s",
                    "webvtt",
                    str(vtt_path),
                ]
            else:
                source = Path(track.path) if track.path else None
                if source is None or not source.exists():
                    continue
                cmd = [
                    require_binary(FFMPEG),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-c:s",
                    "webvtt",
                    str(vtt_path),
                ]
            try:
                await FFmpegRunner(cmd, log_tag=f"opt-sub-{position}").run()
            except FFmpegProcessError:
                continue
            playlist_path = subs_dir / f"s{position}.m3u8"
            self._write_subtitle_playlist(playlist_path, vtt_path, meta)
            subtitle_playlists.append(
                SubtitlePlaylistInfo(
                    index=position,
                    language=track.language or "und",
                    title=track.title or f"Subtitle {position + 1}",
                    forced=track.forced,
                    playlist=f"subtitles/s{position}.m3u8",
                    format="vtt",
                )
            )

        step += 1
        self._progress(step / total_steps, "Writing master playlist")
        master = build_master_playlist(meta, renditions, audio_playlists, subtitle_playlists)
        (out / "master.m3u8").write_text(master, encoding="utf-8")

        meta.optimization.status = "done"
        meta.optimization.path = str(out)
        meta.optimization.renditions = renditions
        meta.optimization.audio = audio_playlists
        meta.optimization.subtitles = subtitle_playlists
        meta.optimization.progress = 1.0
        meta.optimization.error = None
        meta.optimization.updated_at = utcnow_iso()
        meta.updated_at = utcnow_iso()
        write_json(cache.metadata_file(media_id), meta.model_dump(mode="json"))
        self._progress(1.0, "Optimization complete")
        return meta

    @staticmethod
    def _write_subtitle_playlist(playlist_path: Path, vtt_path: Path, meta: Metadata) -> None:
        duration = 3600.0
        if meta.files:
            duration = meta.files[0].duration or 3600.0
        target = max(1, int(math.ceil(duration / 6)))
        lines = [
            "#EXTM3U",
            f"#EXT-X-TARGETDURATION:{target}",
            "#EXT-X-VERSION:3",
            "#EXT-X-MEDIA-SEQUENCE:0",
            f"#EXTINF:{duration:.3f},",
            vtt_path.name,
            "#EXT-X-ENDLIST",
        ]
        playlist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")