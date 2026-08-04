from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_state_store
from app.system.state import StateStore

router = APIRouter(prefix="/api/state", tags=["state"])


def _safe_float(val: object, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@router.get("/watched")
def list_watched(store: StateStore = Depends(get_state_store)) -> dict:
    return {"items": store.all_states()}


@router.get("/recent")
def get_recent(
    limit: int = 12,
    store: StateStore = Depends(get_state_store),
) -> list[dict]:
    states = store.all_states()
    items = []
    for media_id, data in states.items():
        pos = _safe_float(data.get("position"))
        dur = _safe_float(data.get("duration"))
        last = data.get("last_played_at")
        watched = bool(data.get("watched", False))
        if pos > 2 and not watched and (dur <= 0 or pos < dur - 10):
            items.append({
                "media_id": media_id,
                "position": pos,
                "duration": dur,
                "last_played_at": last,
                "progress_pct": round((pos / dur) * 100, 1) if dur > 0 else 0,
            })
    items.sort(key=lambda x: x.get("last_played_at") or "", reverse=True)
    return items[:limit]


@router.get("/{media_id}")
def get_state(media_id: str, store: StateStore = Depends(get_state_store)) -> dict:
    return store.get(media_id).__dict__


@router.post("/{media_id}/watch")
def mark_watched(media_id: str, body: dict | None = None, store: StateStore = Depends(get_state_store)) -> dict:
    watched = body.get("watched", True) if body else True
    return store.mark_watched(media_id, watched).__dict__


@router.post("/{media_id}/progress")
def save_progress(
    media_id: str,
    body: dict,
    store: StateStore = Depends(get_state_store),
) -> dict:
    pos = _safe_float(body.get("position"))
    dur = _safe_float(body.get("duration"))
    return store.progress(media_id, position=pos, duration=dur).__dict__
