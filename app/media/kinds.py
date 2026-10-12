from __future__ import annotations

from enum import Enum


class MediaKind(str, Enum):
    """Every kind of media Quark can index.

    Adding a new vertical (music, photos, ...) means adding a member here and
    registering a builder in :mod:`app.media.registry`. Because this is a
    ``str`` enum, ``item.kind == "movie"`` keeps working everywhere.
    """

    MOVIE = "movie"
    EPISODE = "episode"
    AUDIO = "audio"
    ALBUM = "album"
    ARTIST = "artist"
    PHOTO = "photo"
    VIDEO = "video"  # home videos / other video without movie metadata


class LibraryType(str, Enum):
    """Types of library a user can add."""

    MOVIE = "movie"
    SHOW = "show"
    MUSIC = "music"
    PHOTO = "photo"
    MIXED = "mixed"


#: Which media kinds each library type is expected to produce.
LIBRARY_KINDS: dict[LibraryType, tuple[MediaKind, ...]] = {
    LibraryType.MOVIE: (MediaKind.MOVIE,),
    LibraryType.SHOW: (MediaKind.EPISODE,),
    LibraryType.MUSIC: (MediaKind.ARTIST, MediaKind.ALBUM, MediaKind.AUDIO),
    LibraryType.PHOTO: (MediaKind.PHOTO,),
    LibraryType.MIXED: (
        MediaKind.MOVIE,
        MediaKind.EPISODE,
        MediaKind.VIDEO,
    ),
}


def kinds_for_library(library_type: LibraryType | str) -> tuple[MediaKind, ...]:
    try:
        return LIBRARY_KINDS[LibraryType(library_type)]
    except ValueError:
        return (MediaKind.VIDEO,)
