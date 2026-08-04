from __future__ import annotations

from app.providers.base import ProviderError
from app.providers.fanart import FanArtProvider
from app.providers.opensubtitles import OpenSubtitlesProvider
from app.providers.tmdb import TMDBProvider

_tmdb: TMDBProvider | None = None
_fanart: FanArtProvider | None = None
_opensubtitles: OpenSubtitlesProvider | None = None


def get_tmdb() -> TMDBProvider:
    global _tmdb
    if _tmdb is None:
        from app.config.settings import settings

        _tmdb = TMDBProvider(api_key=settings.data.providers.tmdb.api_key)
    return _tmdb


def get_fanart() -> FanArtProvider:
    global _fanart
    if _fanart is None:
        from app.config.settings import settings

        _fanart = FanArtProvider(api_key=settings.data.providers.fanart.api_key)
    return _fanart


def get_opensubtitles() -> OpenSubtitlesProvider:
    global _opensubtitles
    if _opensubtitles is None:
        from app.config.settings import settings

        config = settings.data.providers.opensubtitles
        _opensubtitles = OpenSubtitlesProvider(
            api_key=config.api_key,
        )
    return _opensubtitles


async def close_providers() -> None:
    providers = [get_tmdb(), get_fanart(), get_opensubtitles()]
    for provider in providers:
        try:
            await provider.close()
        except Exception:
            pass