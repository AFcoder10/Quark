from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_library_service, get_state_store
from app.metadata.models import Metadata
from app.services.library_service import LibraryService
from app.system.state import StateStore

router = APIRouter(prefix="/api/items", tags=["items"])


def _item_summary(item, metadata: Metadata | None, optimized: bool) -> dict:
    data = item.model_dump(mode="json")
    data["display_title"] = item.display_title
    data["has_metadata"] = metadata is not None
    data["optimized"] = optimized
    if metadata is not None:
        data["artwork"] = metadata.artwork
    return data


class ItemQuery(BaseModel):
    model_config = ConfigDict(extra="ignore")

    library_id: str | None = None
    kind: Literal["movie", "episode"] | None = None
    search: str | None = None
    genres: list[str] = Field(default_factory=list)
    unwatched: bool | None = None
    sort: Literal["title", "year", "rating", "recently_added", "recently_watched"] | None = None
    limit: int | None = None
    offset: int = 0


_SORT_KEYS: dict[str, str] = {
    "title": "display_title",
    "year": "year",
    "rating": "_sort_rating",
    "recently_added": "_sort_added",
    "recently_watched": "_sort_watched",
}

_SORT_DESCENDING = {"year", "rating", "recently_added", "recently_watched"}


def _query_enrich(item, service: LibraryService, state_store: StateStore) -> dict | None:
    meta = service.builder.load(item.media_id)
    optimized = bool(meta and meta.optimization.path and Path(meta.optimization.path, "master.m3u8").is_file())
    summary = _item_summary(item, meta, optimized)
    state = state_store.get(item.media_id)
    summary["_sort_rating"] = meta.rating if meta and meta.rating else 0.0
    summary["_sort_added"] = meta.created_at if meta else None
    summary["_sort_watched"] = state.last_played_at
    return summary


@router.api_route("", methods=["QUERY"])
def query_items(
    body: ItemQuery,
    service: LibraryService = Depends(get_library_service),
    state_store: StateStore = Depends(get_state_store),
) -> dict:
    """RFC 10008 QUERY method: safe + idempotent search/filter with a JSON body."""
    items = service.items(library_id=body.library_id, kind=body.kind)
    if body.search:
        query = body.search.lower()
        items = [
            item
            for item in items
            if query in item.title.lower()
            or query in item.display_title.lower()
            or (item.series_title and query in item.series_title.lower())
            or query in item.primary_file.lower()
        ]

    wanted_genres = [genre.strip().lower() for genre in body.genres if genre.strip()]

    enriched: list[dict] = []
    for item in items:
        meta = service.builder.load(item.media_id)
        if wanted_genres and not (
            meta and any(g.lower() in {genre.lower() for genre in meta.genres} for g in wanted_genres)
        ):
            continue
        summary = _query_enrich(item, service, state_store)
        state = state_store.get(item.media_id)
        if body.unwatched is True and state.watched:
            continue
        if body.unwatched is False and not state.watched:
            continue
        enriched.append(summary)

    total = len(enriched)

    if body.sort in _SORT_KEYS:
        key = _SORT_KEYS[body.sort]
        reverse = body.sort in _SORT_DESCENDING
        enriched.sort(
            key=lambda s: (s.get(key) is None, s.get(key) or ""),
            reverse=reverse,
        )

    if body.offset:
        enriched = enriched[body.offset:]
    if body.limit and body.limit > 0:
        enriched = enriched[: body.limit]

    for summary in enriched:
        summary.pop("_sort_rating", None)
        summary.pop("_sort_added", None)
        summary.pop("_sort_watched", None)

    return {"items": enriched, "total": total}


@router.get("")
def list_items(
    library_id: str | None = None,
    kind: str | None = None,
    search: str | None = None,
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    items = service.items(library_id=library_id, kind=kind, search=search)
    result = []
    for item in items:
        meta = service.builder.load(item.media_id)
        optimized = bool(meta and meta.optimization.path and Path(meta.optimization.path, "master.m3u8").is_file())
        result.append(_item_summary(item, meta, optimized))
    return result


@router.get("/genres")
def list_genres(service: LibraryService = Depends(get_library_service)) -> list[str]:
    genres: set[str] = set()
    for item in service.index.all():
        meta = service.builder.load(item.media_id)
        if meta and meta.genres:
            genres.update(meta.genres)
    return sorted(genres)


@router.get("/{media_id}")
def item_detail(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
    client: str | None = None,
) -> dict:
    item = service.item(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    meta = service.builder.load(media_id)
    if meta is not None and client == "android":
        supported, reason = service.builder.direct_play_supported(meta, "android")
        meta.playback.direct_play_supported = supported
        meta.playback.reason = reason
        meta.playback.mode = "direct" if supported else "transcode"
    optimized = False
    if meta and meta.optimization.path:
        optimized = Path(meta.optimization.path, "master.m3u8").is_file()
    data = _item_summary(item, meta, optimized)
    if meta is not None:
        data["metadata"] = meta.model_dump(mode="json")
    return data


@router.get("/{media_id}/metadata")
async def item_metadata(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    meta = await service.metadata(media_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="No metadata found")
    return meta.model_dump(mode="json")


@router.post("/{media_id}/refresh", status_code=202)
def refresh_item(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    item = service.item(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    started = service.refresh(media_id)
    if not started:
        raise HTTPException(status_code=500, detail="Failed to start refresh")
    return {"status": "started", "media_id": media_id}


@router.delete("/{media_id}")
def remove_item(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    item = service.item(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    service.remove_item(media_id)
    return {"status": "removed", "media_id": media_id}


@router.post("/{media_id}/subtitles/download", status_code=202)
def download_subtitles(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    meta = service.builder.load(media_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="No metadata found")
    started = service.download_subtitles(media_id)
    if not started:
        raise HTTPException(status_code=500, detail="Failed to start subtitle download")
    return {"status": "started", "media_id": media_id}