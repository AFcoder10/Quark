from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.media.kinds import MediaKind


class MediaFile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str
    size: int = 0
    extension: str = ""


class MediaItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    media_id: str
    kind: MediaKind = MediaKind.MOVIE
    library_id: str
    title: str
    year: int | None = None
    season: int | None = None
    episode: int | None = None
    series_title: str | None = None
    series_id: int | None = None
    files: list[MediaFile] = []
    primary_file: str = ""

    # music vertical
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: int | None = None
    disc_number: int | None = None
    duration: float | None = None

    # photo vertical
    taken_at: str | None = None

    @property
    def primary(self) -> Path:
        return Path(self.primary_file)

    @property
    def group_key(self) -> str:
        """Key used to group related items (album for tracks, artist for albums)."""
        if self.kind in ("audio", "album"):
            return f"{self.album_artist or self.artist or 'Unknown Artist'}|{self.album or 'Unknown Album'}"
        return self.series_title or self.title

    @property
    def display_title(self) -> str:
        if self.kind == "episode":
            series = self.series_title or self.title
            season = self.season or 0
            episode = self.episode or 0
            return f"{series} S{season:02d}E{episode:02d}"
        if self.kind == "audio":
            if self.track_number is not None:
                return f"{self.track_number:02d}. {self.title}"
            return self.title
        if self.year:
            return f"{self.title} ({self.year})"
        return self.title
