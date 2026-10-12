from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from app.config.libraries import Library
from app.media.models import MediaFile, MediaItem
from app.utils.hashing import media_id_for

PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".tiff",
    ".tif",
    ".heic",
    ".heif",
    ".avif",
}

# RAW formats (metadata only; thumbnails best-effort)
RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}


def is_photo_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in PHOTO_EXTENSIONS or suffix in RAW_EXTENSIONS


def _media_file(path: Path) -> MediaFile:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return MediaFile(path=str(path), size=size, extension=path.suffix.lower().lstrip("."))


def read_exif(path: Path) -> dict:
    """Best-effort EXIF read. Never raises."""
    result: dict = {}
    try:
        from PIL import Image

        with Image.open(path) as img:
            result["width"], result["height"] = img.size
            exif = img.getexif()
            if exif:
                taken = exif.get(36867) or exif.get(306)  # DateTimeOriginal / DateTime
                if taken:
                    result["taken_at"] = _normalize_date(str(taken))
                model = exif.get(272)  # Model
                make = exif.get(271)  # Make
                if make or model:
                    result["camera"] = " ".join(part for part in (make, model) if part).strip()
                gps = _read_gps(exif)
                result.update(gps)
    except Exception:
        pass
    return result


def _normalize_date(value: str) -> str | None:
    value = value.strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d"):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return value or None


def _read_gps(exif) -> dict:
    try:
        gps_ifd = exif.get_ifd(0x8825)
    except Exception:
        return {}
    if not gps_ifd:
        return {}

    def _to_float(values) -> float | None:
        try:
            degrees = float(values[0])
            minutes = float(values[1])
            seconds = float(values[2])
            return degrees + minutes / 60 + seconds / 3600
        except Exception:
            return None

    lat = _to_float(gps_ifd.get(2))
    lon = _to_float(gps_ifd.get(4))
    if lat is not None and str(gps_ifd.get(1, "")).upper().startswith("S"):
        lat = -lat
    if lon is not None and str(gps_ifd.get(3, "")).upper().startswith("W"):
        lon = -lon
    result = {}
    if lat is not None:
        result["latitude"] = lat
    if lon is not None:
        result["longitude"] = lon
    return result


def build_photo_items(library: Library, root: Path) -> list[MediaItem]:
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
            if not is_photo_file(path):
                continue
            media_id = media_id_for("photo", path)
            if media_id in seen:
                continue
            seen.add(media_id)
            items.append(
                MediaItem(
                    media_id=media_id,
                    kind="photo",
                    library_id=library.id,
                    title=path.stem,
                    files=[_media_file(path)],
                    primary_file=str(path),
                )
            )
    return items
