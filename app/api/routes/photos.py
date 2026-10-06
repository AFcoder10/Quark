from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_library_service
from app.services.library_service import LibraryService

router = APIRouter(prefix="/api/photos", tags=["photos"])


def _photo(item, meta=None) -> dict:
    data = {
        "media_id": item.media_id,
        "title": item.title,
        "library_id": item.library_id,
        "primary_file": item.primary_file,
        "taken_at": getattr(meta, "taken_at", None) if meta else None,
        "width": getattr(meta, "width", None) if meta else None,
        "height": getattr(meta, "height", None) if meta else None,
        "camera": getattr(meta, "camera", None) if meta else None,
    }
    return data


@router.get("")
def list_photos(
    library_id: str | None = None,
    limit: int = 500,
    offset: int = 0,
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    items = service.photos(library_id=library_id)
    # newest first when capture date is known
    items = sorted(items, key=lambda i: i.title)
    window = items[offset : offset + limit]
    return [_photo(item, service.builder.load(item.media_id)) for item in window]


@router.get("/{media_id}")
def photo_detail(media_id: str, service: LibraryService = Depends(get_library_service)) -> dict:
    item = service.item(media_id)
    if item is None or item.kind != "photo":
        raise HTTPException(status_code=404, detail="Photo not found")
    meta = service.builder.load(media_id)
    data = _photo(item, meta)
    if meta is not None:
        data["metadata"] = meta.model_dump(mode="json")
    return data
