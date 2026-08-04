from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query

from app.optimization.queue import OptimizationQueue
from app.services.library_service import LibraryService
from app.api.deps import get_optimization_queue, get_library_service
from app.cache.manager import cache

router = APIRouter(prefix="/api", tags=["optimization"])


@router.post("/items/{media_id}/optimize", status_code=202)
def optimize_item(
    media_id: str,
    mode: Literal["hls", "hevc"] = Query(default="hls"),
    queue: OptimizationQueue = Depends(get_optimization_queue),
    service: LibraryService = Depends(get_library_service),
) -> dict:
    from app.config.settings import settings

    if not settings.data.optimization.enabled:
        raise HTTPException(status_code=409, detail="Optimization is disabled")
    item = service.item(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    enqueued = queue.enqueue(media_id, mode=mode)
    return {"status": "queued" if enqueued else "already_pending", "media_id": media_id, "mode": mode}


@router.post("/shows/{show_id}/optimize", status_code=202)
def optimize_show(
    show_id: str,
    mode: Literal["hls", "hevc"] = Query(default="hls"),
    queue: OptimizationQueue = Depends(get_optimization_queue),
    service: LibraryService = Depends(get_library_service),
) -> dict:
    from app.config.settings import settings

    if not settings.data.optimization.enabled:
        raise HTTPException(status_code=409, detail="Optimization is disabled")
    
    episodes = service.index.by_series(show_id)
    if not episodes:
        raise HTTPException(status_code=404, detail="Show not found or has no episodes")
        
    enqueued_count = 0
    for ep in episodes:
        if queue.enqueue(ep.media_id, mode=mode):
            enqueued_count += 1
            
    return {"status": "enqueued", "count": enqueued_count, "total_episodes": len(episodes), "mode": mode}


@router.post("/shows/{show_id}/seasons/{season_num}/optimize", status_code=202)
def optimize_season(
    show_id: str,
    season_num: int,
    mode: Literal["hls", "hevc"] = Query(default="hls"),
    queue: OptimizationQueue = Depends(get_optimization_queue),
    service: LibraryService = Depends(get_library_service),
) -> dict:
    from app.config.settings import settings

    if not settings.data.optimization.enabled:
        raise HTTPException(status_code=409, detail="Optimization is disabled")
    
    all_episodes = service.index.by_series(show_id)
    episodes = [ep for ep in all_episodes if ep.season == season_num]
    if not episodes:
        raise HTTPException(status_code=404, detail="Season not found or has no episodes")
        
    enqueued_count = 0
    for ep in episodes:
        if queue.enqueue(ep.media_id, mode=mode):
            enqueued_count += 1
            
    return {"status": "enqueued", "count": enqueued_count, "total_episodes": len(episodes), "mode": mode}


@router.delete("/items/{media_id}/optimize")
def cancel_optimize(
    media_id: str,
    queue: OptimizationQueue = Depends(get_optimization_queue),
) -> dict:
    queue.cancel(media_id)
    cache.clear_optimized(media_id)
    return {"status": "cancelled", "media_id": media_id}


@router.get("/optimize/queue")
def optimize_queue(queue: OptimizationQueue = Depends(get_optimization_queue)) -> dict:
    return {"jobs": queue.all()}


@router.get("/items/{media_id}/optimize/status")
def optimize_status(
    media_id: str,
    queue: OptimizationQueue = Depends(get_optimization_queue),
) -> dict:
    status = queue.status(media_id)
    if status is None:
        return {"media_id": media_id, "status": "none"}
    return status