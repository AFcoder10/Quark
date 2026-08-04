from __future__ import annotations

from app.providers.base import BaseProvider, ProviderError


class FanArtProvider(BaseProvider):
    name = "fanart"
    BASE_URL = "https://webservice.fanart.tv/v3"

    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        super().__init__(timeout=timeout)
        self.api_key = api_key

    def _require_key(self) -> None:
        if not self.api_key:
            raise ProviderError("FanArt.tv API key not configured")

    async def movie_art(self, tmdb_id: int) -> dict:
        self._require_key()
        return await self._get_json(f"{self.BASE_URL}/movies/{tmdb_id}", params={"api_key": self.api_key})

    async def tv_art(self, tmdb_id: int) -> dict:
        self._require_key()
        return await self._get_json(f"{self.BASE_URL}/tv/{tmdb_id}", params={"api_key": self.api_key})