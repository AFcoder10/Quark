from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.cache.manager import cache
from app.metadata.models import ArtworkMapping, Metadata
from app.providers import get_fanart, get_tmdb

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

_MOVIE_FANART_MAP = {
    "movieposter": "poster",
    "moviebackground": "backdrop",
    "hdlogo": "logo",
    "logo": "logo",
    "hdclearart": "clearart",
    "clearart": "clearart",
    "disc": "disc",
    "banner": "banner",
    "moviethumb": "thumb",
}

_TV_FANART_MAP = {
    "tvposter": "poster",
    "showbackground": "backdrop",
    "hdtvlogo": "logo",
    "clearlogo": "clearlogo",
    "hdclearart": "clearart",
    "clearart": "clearart",
    "disc": "disc",
    "tvbanner": "banner",
    "seasonbanner": "landscape",
    "seasonposter": "poster",
    "tvthumb": "thumb",
}


def _extension_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if path.endswith(ext):
            return ext
    return ".jpg"


def _lang_score(lang: str | None) -> int:
    if not lang:
        return 2
    l = lang.lower()
    if l == "en":
        return 3
    if l in ("00", "xx", "null"):
        return 2
    return 1


class ArtworkManager:
    ART_TYPES = ("poster", "backdrop", "logo", "clearlogo", "clearart", "disc", "banner", "landscape", "thumb", "still")

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Quark/0.1"})
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_and_cache(self, meta: Metadata) -> ArtworkMapping:
        out = cache.artwork_dir(meta.media_id)
        out.mkdir(parents=True, exist_ok=True)
        candidates = await self._collect_candidates(meta)
        mapping = ArtworkMapping()
        for art_type in self.ART_TYPES:
            existing = next(out.glob(f"{art_type}.*"), None)
            if existing is not None:
                setattr(mapping, art_type, str(existing))
                continue
            for url in candidates.get(art_type, []):
                target = out / f"{art_type}{_extension_from_url(url)}"
                if await self._download(url, target):
                    setattr(mapping, art_type, str(target))
                    break
        return mapping

    async def _collect_candidates(self, meta: Metadata) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        if not meta.tmdb_id:
            return dict(result)

        fanart_map = _TV_FANART_MAP if meta.kind == "episode" else _MOVIE_FANART_MAP
        try:
            fanart_tv_id = meta.tvdb_id if meta.kind == "episode" else meta.tmdb_id
            if fanart_tv_id:
                data = await get_fanart().tv_art(fanart_tv_id) if meta.kind == "episode" else await get_fanart().movie_art(meta.tmdb_id)
                for key, art_type in fanart_map.items():
                    entries = data.get(key) or []
                    entries = sorted(entries, key=lambda entry: (_lang_score(entry.get("lang")), entry.get("likes", 0)), reverse=True)
                    for entry in entries[:5]:
                        url = entry.get("url")
                        if url and url not in result[art_type]:
                            result[art_type].append(url)
        except Exception:
            pass

        try:
            images = await get_tmdb().tv_images(meta.tmdb_id) if meta.kind == "episode" else await get_tmdb().movie_images(meta.tmdb_id)
            for image in images.get("posters", []):
                file_path = image.get("file_path")
                if file_path:
                    result["poster"].append(f"{TMDB_IMAGE_BASE}{file_path}")
            for image in images.get("backdrops", []):
                file_path = image.get("file_path")
                if file_path:
                    result["backdrop"].append(f"{TMDB_IMAGE_BASE}{file_path}")
            for image in sorted(images.get("logos", []), key=lambda item: (_lang_score(item.get("iso_639_1")), item.get("vote_average", 0)), reverse=True):
                file_path = image.get("file_path")
                if file_path and not file_path.endswith(".svg"):
                    url = f"{TMDB_IMAGE_BASE}{file_path}"
                    if url not in result["logo"]:
                        result["logo"].append(url)
                    if url not in result["clearlogo"]:
                        result["clearlogo"].append(url)
        except Exception:
            pass

        return dict(result)

    async def _download(self, url: str, target: Path) -> bool:
        try:
            response = await self.client.get(url)
        except httpx.HTTPError:
            return False
        if response.status_code != 200 or not response.content:
            return False
        try:
            target.write_bytes(response.content)
        except OSError:
            return False
        return True