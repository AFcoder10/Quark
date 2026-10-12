from __future__ import annotations

from pathlib import Path

import pytest

from app.media.kinds import LibraryType, MediaKind, kinds_for_library
from app.media.models import MediaItem
from app.media.registry import build_items, get_builder
from app.config.libraries import Library


def test_media_kind_str_equality():
    assert MediaKind.MOVIE == "movie"
    assert MediaKind.EPISODE == "episode"
    assert MediaKind.AUDIO == "audio"


def test_library_type_accepts_new_and_legacy_values():
    assert LibraryType.MUSIC == "music"
    assert LibraryType.PHOTO == "photo"
    assert LibraryType.MIXED == "mixed"


def test_kinds_for_library():
    assert MediaKind.MOVIE in kinds_for_library("movie")
    assert MediaKind.EPISODE in kinds_for_library("show")
    assert kinds_for_library("unknown") == (MediaKind.VIDEO,)


def test_registry_has_builders():
    for lib_type in ("movie", "show", "mixed"):
        assert get_builder(lib_type) is not None


def test_movie_library_builds_items(tmp_path: Path):
    (tmp_path / "a.mp4").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("n")
    lib = Library(id="L", name="Movies", path=str(tmp_path), type="movie")
    items = build_items(lib, tmp_path)
    assert len(items) == 1
    assert items[0].kind == "movie"
    assert items[0].title


def test_mixed_library_builds_movies_and_shows(tmp_path: Path):
    movies = tmp_path / "movies"
    stops = tmp_path / "shows"
    movies.mkdir()
    (movies / "Some_Movie_2010_1080p.mp4").write_bytes(b"x")
    (stops / "The Wire" / "S01").mkdir(parents=True)
    (stops / "The Wire" / "S01" / "ep1.mp4").write_bytes(b"x")

    lib = Library(id="L", name="Mixed", path=str(tmp_path), type="mixed")
    items = build_items(lib, tmp_path)
    kinds = {i.kind for i in items}
    assert "movie" in kinds
    assert "episode" in kinds
