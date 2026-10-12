from __future__ import annotations

from pathlib import Path

from app.cache.manager import cache

THUMB_MAX = 480


def thumbnail_path(media_id: str) -> Path:
    return cache.artwork_dir(media_id) / "thumb.webp"


def ensure_thumbnail(media_id: str, source: Path, *, size: int = THUMB_MAX) -> Path | None:
    """Generate (and cache) a web-friendly thumbnail for an image."""
    if not source.is_file():
        return None
    target = thumbnail_path(media_id)
    if target.is_file() and target.stat().st_size > 0:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageOps

        with Image.open(source) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((size, size))
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            img.save(target, "WEBP", quality=82, method=4)
    except Exception:
        return None
    return target if target.is_file() else None
