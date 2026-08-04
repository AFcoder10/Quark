from __future__ import annotations

import httpx


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseProvider:
    name = "base"

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Quark/0.1.0 (Quark Media Server; https://github.com/quark)",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get_json(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> dict:
        try:
            response = await self.client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} request failed: {exc}") from exc
        if response.status_code != 200:
            raise ProviderError(f"{self.name} returned HTTP {response.status_code}", response.status_code)
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise ProviderError(
                f"{self.name} returned non-JSON response "
                f"(HTTP {response.status_code}, content-type: {content_type or 'none'})"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.name} returned malformed JSON") from exc

    async def _post_json(self, url: str, *, json: dict | None = None, headers: dict | None = None) -> dict:
        try:
            response = await self.client.post(url, json=json, headers=headers)
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} request failed: {exc}") from exc
        if response.status_code != 200:
            raise ProviderError(f"{self.name} returned HTTP {response.status_code}", response.status_code)
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise ProviderError(
                f"{self.name} returned non-JSON response "
                f"(HTTP {response.status_code}, content-type: {content_type or 'none'})"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.name} returned malformed JSON") from exc

    async def _get_bytes(self, url: str, *, headers: dict | None = None) -> bytes:
        try:
            response = await self.client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} download failed: {exc}") from exc
        if response.status_code != 200:
            raise ProviderError(f"{self.name} returned HTTP {response.status_code}", response.status_code)
        return response.content