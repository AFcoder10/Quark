from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

from app.utils.json_utils import read_json, write_json

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

DIRECT_PLAY_CODECS = ["h264", "avc", "h.264"]
DIRECT_PLAY_CONTAINERS = ["mp4", "mkv", "mov", "m4v", "webm", "ts", "m2ts", "avi", "flv"]


class ServerSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8090
    log_level: str = "INFO"
    scan_on_startup: bool = False


class StreamingSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    default_mode: Literal["auto", "direct", "hls", "transcode"] = "direct"
    direct_play_codecs: list[str] = Field(default_factory=lambda: list(DIRECT_PLAY_CODECS))
    direct_play_containers: list[str] = Field(default_factory=lambda: list(DIRECT_PLAY_CONTAINERS))
    live_transcode_height: int = 1080
    live_idle_seconds: int = 60
    subtitle_size: int = 22
    subtitle_bg: bool = True


class OptimizationSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    renditions: list[str] = Field(
        default_factory=lambda: ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
    )
    segment_seconds: int = 6
    video_codec: str = "libx264"
    crf: int = 23
    preset: str = "veryfast"
    audio_copy_codecs: list[str] = Field(default_factory=lambda: ["aac", "ac3", "eac3", "mp3"])
    subtitle_format: str = "webvtt"


class TMDBConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    api_key: str = ""


class FanArtConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    api_key: str = ""


class OpenSubtitlesConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    api_key: str = ""
    languages: list[str] = Field(default_factory=lambda: ["en"])


class ProvidersSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tmdb: TMDBConfig = TMDBConfig()
    fanart: FanArtConfig = FanArtConfig()
    opensubtitles: OpenSubtitlesConfig = OpenSubtitlesConfig()


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    server: ServerSettings = ServerSettings()
    streaming: StreamingSettings = StreamingSettings()
    optimization: OptimizationSettings = OptimizationSettings()
    providers: ProvidersSettings = ProvidersSettings()


class SettingsManager:
    def __init__(self) -> None:
        self.data = Settings()

    @property
    def path(self) -> Path:
        return BASE_DIR / "config" / "settings.json"

    def load(self) -> Settings:
        raw = read_json(self.path)
        if raw is None:
            self.save()
        else:
            self.data = Settings.model_validate(raw)
        self._apply_env_overrides()
        return self.data

    def _apply_env_overrides(self) -> None:
        tmdb_key = os.environ.get("TMDB_API_KEY", "")
        if tmdb_key:
            self.data.providers.tmdb.api_key = tmdb_key
        fanart_key = os.environ.get("FANART_API_KEY", "")
        if fanart_key:
            self.data.providers.fanart.api_key = fanart_key
        osub_api_key = os.environ.get("OPENSUBTITLES_API_KEY", "")
        osub_langs = os.environ.get("OPENSUBTITLES_LANGUAGES", "en")
        if osub_api_key:
            self.data.providers.opensubtitles.enabled = True
            self.data.providers.opensubtitles.api_key = osub_api_key
        if osub_langs:
            self.data.providers.opensubtitles.languages = [
                lang.strip() for lang in osub_langs.split(",") if lang.strip()
            ]

    def save(self) -> None:
        write_json(self.path, self.data.model_dump(mode="json"))

    def reload(self) -> Settings:
        return self.load()

    def update(self, data: dict) -> Settings:
        self.data = Settings.model_validate(data)
        self.save()
        return self.data


settings = SettingsManager()