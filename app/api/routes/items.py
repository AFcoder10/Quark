from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.metadata.models import Metadata
from app.services.library_service import LibraryService
from app.api.deps import get_library_service

router = APIRouter(prefix="/api/items", tags=["items"])


def _item_summary(item, metadata: Metadata | None, optimized: bool) -> dict:
    data = item.model_dump(mode="json")
    data["display_title"] = item.display_title
    data["has_metadata"] = metadata is not None
    data["optimized"] = optimized
    if metadata is not None:
        data["artwork"] = metadata.artwork
    return data


@router.get("")
def list_items(
    library_id: str | None = None,
    kind: str | None = None,
    search: str | None = None,
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    from app.cache.manager import cache

    items = service.items(library_id=library_id, kind=kind, search=search)
    result = []
    for item in items:
        meta = service.builder.load(item.media_id)
        optimized = False
        if meta and meta.optimization.path:
            optimized = Path(meta.optimization.path, "master.m3u8").is_file()
        result.append(_item_summary(item, meta, optimized))
    return result


@router.get("/{media_id}")
def item_detail(
    media_id: str,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    item = service.item(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    meta = service.builder.load(media_id)
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