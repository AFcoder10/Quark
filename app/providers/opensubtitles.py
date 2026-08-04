from __future__ import annotations

import httpx

from app.providers.base import BaseProvider, ProviderError


class OpenSubtitlesProvider(BaseProvider):
    name = "opensubtitles"
    BASE_URL = "https://api.opensubtitles.com/api/v1"

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)
        self.api_key = api_key
        self._token: str | None = None

    def _auth_headers(self) -> dict:
        return {"Api-Key": self.api_key}

    async def search(
        self,
        *,
        tmdb_id: int | None = None,
        imdb_id: str | None = None,
        kind: str = "movie",
        season: int | None = None,
        episode: int | None = None,
        languages: list[str] | None = None,
    ) -> list[dict]:
        if not self.api_key:
            raise ProviderError("OpenSubtitles API key not configured")
        params: dict = {"languages": ",".join(languages or ["en"])}
        if tmdb_id:
            params["tmdb_id"] = tmdb_id
        if imdb_id:
            params["imdb_id"] = imdb_id
        if kind == "tv":
            params["type"] = "tv"
            if season is not None:
                params["season_number"] = season
            if episode is not None:
                params["episode_number"] = episode
        else:
            params["type"] = "movie"
        try:
            data = await self._get_json(f"{self.BASE_URL}/subtitles", params=params, headers=self._auth_headers())
        except ProviderError:
            raise
        return data.get("data", [])

    async def download(self, file_id: int) -> tuple[bytes, str]:
        if not self.api_key:
            raise ProviderError("OpenSubtitles API key not configured")
        try:
            data = await self._get_json(
                f"{self.BASE_URL}/download",
                params={"file_id": file_id},
                headers=self._auth_headers(),
            )
        except ProviderError:
            raise
        link = data.get("link")
        file_name = data.get("file_name", "subtitle")
        if not link:
            raise ProviderError("OpenSubtitles download returned no link")
        try:
            content = await self._get_bytes(link)
        except ProviderError:
            raise
        return content, file_name