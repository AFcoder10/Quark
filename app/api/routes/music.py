from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_library_service
from app.services.library_service import LibraryService

router = APIRouter(prefix="/api/music", tags=["music"])


def _track(item) -> dict:
    return {
        "media_id": item.media_id,
        "title": item.title,
        "artist": item.artist,
        "album": item.album,
        "album_artist": item.album_artist,
        "track_number": item.track_number,
        "disc_number": item.disc_number,
        "duration": item.duration,
        "display_title": item.display_title,
        "library_id": item.library_id,
    }


@router.get("")
def list_artists(service: LibraryService = Depends(get_library_service)) -> list[dict]:
    return service.artists()


@router.get("/albums")
def list_albums(
    artist: str | None = None,
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    return service.albums(artist=artist)


@router.get("/album")
def album_tracks(
    artist: str,
    album: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    tracks = service.album_tracks(artist, album)
    if not tracks:
        raise HTTPException(status_code=404, detail="Album not found")
    return {
        "artist": artist,
        "album": album,
        "tracks": [_track(t) for t in tracks],
    }


@router.get("/tracks")
def list_tracks(
    artist: str | None = None,
    album: str | None = None,
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    if artist and album:
        return [_track(t) for t in service.album_tracks(artist, album)]
    tracks = [item for item in service.index.all() if item.kind == "audio"]
    if artist:
        tracks = [t for t in tracks if (t.album_artist or t.artist) == artist]
    if album:
        tracks = [t for t in tracks if t.album == album]
    return [_track(t) for t in sorted(tracks, key=lambda t: (t.album or "", t.disc_number or 0, t.track_number or 0))]
