from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ArtworkMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")

    poster: str | None = None
    backdrop: str | None = None
    logo: str | None = None
    clearlogo: str | None = None
    clearart: str | None = None
    disc: str | None = None
    banner: str | None = None
    landscape: str | None = None
    thumb: str | None = None
    still: str | None = None


class FileInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str
    size: int = 0
    extension: str = ""
    container: str | None = None
    duration: float | None = None


class VideoInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    codec: str | None = None
    width: int | None = None
    height: int | None = None
    bitrate: int | None = None
    fps: float | None = None
    profile: str | None = None
    level: str | None = None
    pixel_format: str | None = None
    color_space: str | None = None


class AudioTrackInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    index: int | None = None
    codec: str | None = None
    language: str | None = None
    channels: int | None = None
    sample_rate: int | None = None
    bitrate: int | None = None
    title: str | None = None
    profile: str | None = None


class SubtitleTrackInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    index: int | None = None
    codec: str | None = None
    language: str | None = None
    title: str | None = None
    forced: bool = False
    default: bool = False
    embedded: bool = True
    format: str | None = None
    path: str | None = None


class ChapterInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    index: int = 0
    time: float = 0.0
    title: str = ""


class RenditionInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    height: int
    width: int
    bitrate: int
    playlist: str


class AudioPlaylistInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    index: int
    language: str
    title: str
    playlist: str
    codec: str = "aac"


class SubtitlePlaylistInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    index: int
    language: str
    title: str
    forced: bool = False
    playlist: str
    format: str = "vtt"


class OptimizationInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["none", "pending", "processing", "done", "failed"] = "none"
    enabled: bool = True
    path: str | None = None
    renditions: list[RenditionInfo] = Field(default_factory=list)
    audio: list[AudioPlaylistInfo] = Field(default_factory=list)
    subtitles: list[SubtitlePlaylistInfo] = Field(default_factory=list)
    progress: float = 0.0
    error: str | None = None
    updated_at: str | None = None
    created_at: str | None = None


class PlaybackInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: Literal["direct", "hls", "transcode"] | None = None
    direct_play_supported: bool = False
    reason: str = ""


class Metadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: int = 1
    media_id: str
    kind: Literal["movie", "episode"] = "movie"
    library_id: str
    title: str
    original_title: str | None = None
    year: int | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = None
    tvdb_id: int | None = None
    overview: str | None = None
    rating: float | None = None
    vote_count: int | None = None
    popularity: float | None = None
    genres: list[str] = Field(default_factory=list)
    runtime: int | None = None
    season: int | None = None
    episode: int | None = None
    series_title: str | None = None
    series_id: int | None = None
    air_date: str | None = None
    first_air_date: str | None = None
    last_air_date: str | None = None
    status: str | None = None
    tagline: str | None = None
    certification: str | None = None
    networks: list[str] = Field(default_factory=list)
    creators: list[str] = Field(default_factory=list)
    production_companies: list[str] = Field(default_factory=list)
    spoken_languages: list[str] = Field(default_factory=list)
    number_of_seasons: int | None = None
    number_of_episodes: int | None = None
    files: list[FileInfo] = Field(default_factory=list)
    primary_file: str = ""
    video: VideoInfo | None = None
    audio: list[AudioTrackInfo] = Field(default_factory=list)
    subtitles: list[SubtitleTrackInfo] = Field(default_factory=list)
    chapters: list[ChapterInfo] = Field(default_factory=list)
    artwork: ArtworkMapping = ArtworkMapping()
    optimization: OptimizationInfo = OptimizationInfo()
    playback: PlaybackInfo = PlaybackInfo()
    created_at: str | None = None
    updated_at: str | None = None

    def has_tmdb(self) -> bool:
        if not self.tmdb_id:
            return False
        if self.kind == "episode":
            return bool(self.overview) or (bool(self.title) and not self.title.startswith(self.series_title or ""))
        return bool(self.overview) or bool(self.artwork.poster)