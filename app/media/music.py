from __future__ import annotations

import os
from pathlib import Path

from mutagen import File as MutagenFile

from app.config.libraries import Library
from app.media.models import MediaFile, MediaItem
from app.utils.hashing import media_id_for

AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".oga",
    ".opus",
    ".wav",
    ".wma",
    ".aiff",
    ".ape",
    ".alac",
}


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def _media_file(path: Path) -> MediaFile:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return MediaFile(path=str(path), size=size, extension=path.suffix.lower().lstrip("."))


def _first(tags, *keys: str) -> str | None:
    for key in keys:
        value = tags.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)) and value:
            return str(value[0])
        return str(value)
    return None


def _as_int(value: str | None) -> int | None:
    if not value:
        return None
    # tags like "3/12"
    value = str(value).split("/")[0].strip()
    try:
        return int(value)
    except ValueError:
        return None


def read_tags(path: Path) -> dict:
    """Read audio tags via mutagen, tolerant of malformed files."""
    try:
        audio = MutagenFile(path, easy=True)
    except Exception:
        audio = None
    tags = audio.tags if audio is not None and audio.tags else {}

    info = getattr(audio, "info", None)
    duration = float(getattr(info, "length", 0.0) or 0.0) if info is not None else None

    return {
        "title": _first(tags, "title") or path.stem,
        "artist": _first(tags, "artist", "albumartist"),
        "album": _first(tags, "album"),
        "album_artist": _first(tags, "albumartist", "artist"),
        "track_number": _as_int(_first(tags, "tracknumber")),
        "disc_number": _as_int(_first(tags, "discnumber")),
        "genre": _first(tags, "genre"),
        "duration": duration,
    }


def build_music_items(library: Library, root: Path) -> list[MediaItem]:
    """Scan a music library into track items.

    Layout is flexible — artist/album folders are inferred from tags, not
    the directory tree, so flat collections work too.
    """
    items: list[MediaItem] = []
    if not root.is_dir():
        return items

    seen: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            path = Path(dirpath) / name
            if not is_audio_file(path):
                continue
            tags = read_tags(path)
            media_id = media_id_for("audio", path)
            if media_id in seen:
                continue
            seen.add(media_id)
            items.append(
                MediaItem(
                    media_id=media_id,
                    kind="audio",
                    library_id=library.id,
                    title=tags["title"],
                    artist=tags["artist"],
                    album=tags["album"],
                    album_artist=tags["album_artist"],
                    track_number=tags["track_number"],
                    disc_number=tags["disc_number"],
                    duration=tags["duration"],
                    files=[_media_file(path)],
                    primary_file=str(path),
                )
            )
    return items
