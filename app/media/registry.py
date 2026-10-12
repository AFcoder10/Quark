from __future__ import annotations

from pathlib import Path

from app.config.libraries import Library
from app.media.kinds import LibraryType
from app.media.models import MediaItem

#: Builder signature: (library, root) -> list[MediaItem]
#:
#: To add a new vertical (music, photos, ...):
#:   1. add a MediaKind + LibraryType in app/media/kinds.py
#:   2. write build_<type>_items(library, root) -> list[MediaItem]
#:   3. register it in BUILDERS below
#: The scanner and metadata pipeline pick it up automatically.


def _movie_builder(library: Library, root: Path) -> list[MediaItem]:
    from app.media.detection import build_movie_items, is_media_file

    files = [p for p in root.rglob("*") if p.is_file() and is_media_file(p)] if root.is_dir() else []
    return build_movie_items(library, files)


def _show_builder(library: Library, root: Path) -> list[MediaItem]:
    from app.media.detection import build_tvshow_items

    return build_tvshow_items(library, root)


def _mixed_builder(library: Library, root: Path) -> list[MediaItem]:
    """Handle folders that contain both movies and shows."""
    from app.media.detection import build_movie_items, build_tvshow_items, is_media_file

    if not root.is_dir():
        return []
    items: list[MediaItem] = []
    show_dirs = [
        p
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and any(d.is_dir() for d in p.iterdir())
    ]
    if show_dirs:
        items.extend(build_tvshow_items(library, root))
    files = [p for p in root.rglob("*") if p.is_file() and is_media_file(p)]
    if files:
        items.extend(build_movie_items(library, files))
    return items


def _photo_builder(library: Library, root: Path) -> list[MediaItem]:
    from app.media.photo import build_photo_items

    return build_photo_items(library, root)


def _music_builder(library: Library, root: Path) -> list[MediaItem]:
    from app.media.music import build_music_items

    return build_music_items(library, root)


BUILDERS = {
    LibraryType.MOVIE.value: _movie_builder,
    LibraryType.SHOW.value: _show_builder,
    LibraryType.MUSIC.value: _music_builder,
    LibraryType.PHOTO.value: _photo_builder,
    LibraryType.MIXED.value: _mixed_builder,
}


def get_builder(library_type: str):
    return BUILDERS.get(library_type, _movie_builder)


def build_items(library: Library, root: Path) -> list[MediaItem]:
    """Detect and build media items for a library using its registered builder."""
    return get_builder(library.type)(library, root)
