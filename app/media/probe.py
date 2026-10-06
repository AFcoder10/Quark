from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.system.commands import FFPROBE, require_binary, run_async


@dataclass
class ProbeVideo:
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    bitrate: int | None = None
    fps: float | None = None
    profile: str | None = None
    level: int | None = None
    pixel_format: str | None = None
    color_space: str | None = None


@dataclass
class ProbeAudio:
    index: int | None = None
    codec: str | None = None
    language: str | None = None
    channels: int | None = None
    sample_rate: int | None = None
    bitrate: int | None = None
    title: str | None = None
    profile: str | None = None


@dataclass
class ProbeSubtitle:
    index: int | None = None
    codec: str | None = None
    language: str | None = None
    title: str | None = None
    forced: bool = False
    default: bool = False
    format: str | None = None


@dataclass
class ProbeChapter:
    index: int = 0
    time: float = 0.0
    title: str = ""


@dataclass
class ProbeResult:
    container: str | None = None
    duration: float | None = None
    video: ProbeVideo | None = None
    audio: list[ProbeAudio] = field(default_factory=list)
    subtitles: list[ProbeSubtitle] = field(default_factory=list)
    chapters: list[ProbeChapter] = field(default_factory=list)


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_fraction(value: str | None) -> float | None:
    if not value or value in ("0/0", "N/A"):
        return None
    if "/" in value:
        numerator, _, denominator = value.partition("/")
        try:
            den = float(denominator)
            if den == 0:
                return None
            return round(float(numerator) / den, 3)
        except ValueError:
            return None
    return _as_float(value)


def _parse_streams(data: dict[str, Any]) -> ProbeResult:
    streams: list[dict[str, Any]] = data.get("streams") or []
    result = ProbeResult()

    fmt = data.get("format") or {}
    result.duration = _as_float(fmt.get("duration"))
    container = fmt.get("format_name")
    if container:
        result.container = container.split(",")[0]

    for stream in streams:
        codec_type = stream.get("codec_type")
        tags = stream.get("tags") or {}
        disposition = stream.get("disposition") or {}

        if codec_type == "video" and result.video is None:
            result.video = ProbeVideo(
                codec=stream.get("codec_name"),
                width=_as_int(stream.get("width")),
                height=_as_int(stream.get("height")),
                bitrate=_as_int(stream.get("bit_rate")),
                fps=_parse_fraction(stream.get("avg_frame_rate")) or _parse_fraction(stream.get("r_frame_rate")),
                profile=stream.get("profile"),
                level=_as_int(stream.get("level")),
                pixel_format=stream.get("pix_fmt"),
                color_space=stream.get("color_space"),
            )
        elif codec_type == "audio":
            result.audio.append(
                ProbeAudio(
                    index=_as_int(stream.get("index")),
                    codec=stream.get("codec_name"),
                    language=tags.get("language"),
                    channels=_as_int(stream.get("channels")),
                    sample_rate=_as_int(stream.get("sample_rate")),
                    bitrate=_as_int(stream.get("bit_rate")),
                    title=tags.get("title"),
                    profile=stream.get("profile"),
                )
            )
        elif codec_type == "subtitle":
            result.subtitles.append(
                ProbeSubtitle(
                    index=_as_int(stream.get("index")),
                    codec=stream.get("codec_name"),
                    language=tags.get("language"),
                    title=tags.get("title"),
                    forced=bool(disposition.get("forced")),
                    default=bool(disposition.get("default")),
                    format=stream.get("codec_name"),
                )
            )

    for position, chapter in enumerate(data.get("chapters") or []):
        tags = chapter.get("tags") or {}
        result.chapters.append(
            ProbeChapter(
                index=position,
                time=_as_float(chapter.get("start_time")) or 0.0,
                title=tags.get("title") or f"Chapter {position + 1}",
            )
        )

    return result


async def probe_media(path: Path) -> ProbeResult:
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")
    args = [
        require_binary(FFPROBE),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        "-show_chapters",
        str(path),
    ]
    completed = await run_async(args, timeout=120)
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip() if completed.stderr else ""
        raise RuntimeError(f"ffprobe failed for {path}: {detail}")
    try:
        data = json.loads(completed.stdout.decode("utf-8", errors="replace"))
    except ValueError as exc:
        raise RuntimeError(f"Invalid ffprobe output for {path}") from exc
    return _parse_streams(data)
