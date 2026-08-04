from __future__ import annotations

from app.providers.base import BaseProvider, ProviderError


class TMDBProvider(BaseProvider):
    name = "tmdb"
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        super().__init__(timeout=timeout)
        self.api_key = api_key
        self._cache: dict[str, dict] = {}

    def _require_key(self) -> None:
        if not self.api_key:
            raise ProviderError("TMDB API key not configured")

    async def _get(self, endpoint: str, **params) -> dict:
        cache_key = endpoint + str(sorted(params.items()))
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        self._require_key()
        data = await self._get_json(f"{self.BASE_URL}{endpoint}", params={**params, "api_key": self.api_key})
        self._cache[cache_key] = data
        return data

    async def search_movie(self, query: str, year: int | None = None) -> list[dict]:
        params: dict = {"query": query}
        if year:
            params["year"] = year
        data = await self._get("/search/movie", **params)
        return data.get("results", [])

    async def search_tv(self, query: str) -> list[dict]:
        data = await self._get("/search/tv", query=query)
        return data.get("results", [])

    async def movie_details(self, movie_id: int) -> dict:
        return await self._get(f"/movie/{movie_id}")

    async def tv_details(self, tv_id: int) -> dict:
        return await self._get(f"/tv/{tv_id}")

    async def episode_details(self, tv_id: int, season: int, episode: int) -> dict:
        return await self._get(f"/tv/{tv_id}/season/{season}/episode/{episode}")

    async def season_details(self, tv_id: int, season: int) -> dict:
        return await self._get(f"/tv/{tv_id}/season/{season}")

    async def movie_images(self, movie_id: int) -> dict:
        return await self._get(f"/movie/{movie_id}/images")

    async def tv_images(self, tv_id: int) -> dict:
        return await self._get(f"/tv/{tv_id}/images")

    async def movie_external_ids(self, movie_id: int) -> dict:
        return await self._get(f"/movie/{movie_id}/external_ids")

    async def tv_external_ids(self, tv_id: int) -> dict:
        return await self._get(f"/tv/{tv_id}/external_ids")

    async def find_movie(self, query: str, year: int | None = None) -> dict | None:
        results = await self.search_movie(query, year)
        if not results:
            return None
        return await self.movie_details(results[0]["id"])

    async def find_tv(self, query: str) -> dict | None:
        results = await self.search_tv(query)
        if not results:
            return None
        return await self.tv_details(results[0]["id"])