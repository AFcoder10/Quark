from __future__ import annotations

import os
from pathlib import Path

from app.config.libraries import Library
from app.media.models import MediaFile, MediaItem
from app.utils.filenames import (
    clean_title,
    extract_year,
    is_season_dir,
    parse_episode,
    parse_episode_number,
    parse_season_from_dir,
    strip_episode_token,
)
from app.utils.hashing import media_id_for

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".m4v",
    ".webm",
    ".ts",
    ".m2ts",
    ".avi",
    ".flv",
    ".wmv",
    ".mpg",
    ".mpeg",
    ".m2v",
    ".vob",
    ".3gp",
    ".ogv",
}


def is_media_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def _media_file(path: Path) -> MediaFile:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return MediaFile(path=str(path), size=size, extension=path.suffix.lower().lstrip("."))


def _iter_video_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            candidate = Path(dirpath) / name
            if is_media_file(candidate):
                found.append(candidate)
    return found


def _movie_item(library: Library, path: Path) -> MediaItem:
    title = clean_title(path.stem) or path.stem
    return MediaItem(
        media_id=media_id_for("movie", path),
        kind="movie",
        library_id=library.id,
        title=title,
        year=extract_year(path.stem),
        files=[_media_file(path)],
        primary_file=str(path),
    )


def build_movie_items(library: Library, files: list[Path]) -> list[MediaItem]:
    items: list[MediaItem] = []
    seen: set[str] = set()
    for path in sorted(files):
        if not is_media_file(path):
            continue
        item = _movie_item(library, path)
        if item.media_id in seen:
            continue
        seen.add(item.media_id)
        items.append(item)
    return items


def _episode_item(
    library: Library,
    series_title: str,
    path: Path,
    season: int | None,
    episode: int | None,
) -> MediaItem:
    stem = path.stem
    title = clean_title(strip_episode_token(stem))
    if not title:
        title = f"Episode {episode}" if episode is not None else stem
    return MediaItem(
        media_id=media_id_for("episode", path),
        kind="episode",
        library_id=library.id,
        title=title,
        year=extract_year(stem),
        season=season,
        episode=episode,
        series_title=series_title,
        files=[_media_file(path)],
        primary_file=str(path),
    )


def _resolve_episode(path: Path, dir_season: int | None) -> tuple[int | None, int | None]:
    parsed = parse_episode(path.stem)
    if parsed is not None:
        return parsed
    return dir_season, parse_episode_number(path.stem)


def build_tvshow_items(library: Library, root: Path) -> list[MediaItem]:
    """Build episode items from the strict TV layout::

        <show name>/<season dir>/<episode files>

    Loose files directly inside the show directory are supported as a
    fallback when no season directories exist.
    """
    items: list[MediaItem] = []
    if not root.is_dir():
        return items

    show_dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    for show_dir in show_dirs:
        series_title = show_dir.name
        season_dirs = sorted(p for p in show_dir.iterdir() if p.is_dir() and is_season_dir(p.name))

        if season_dirs:
            for season_dir in season_dirs:
                dir_season = parse_season_from_dir(season_dir.name)
                for path in _iter_video_files(season_dir):
                    season, episode = _resolve_episode(path, dir_season)
                    items.append(_episode_item(library, series_title, path, season, episode))
        else:
            for path in _iter_video_files(show_dir):
                season, episode = _resolve_episode(path, None)
                items.append(_episode_item(library, series_title, path, season, episode))

    return items
