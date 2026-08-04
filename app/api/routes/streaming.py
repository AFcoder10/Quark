from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.services.playback_service import PlaybackService
from app.api.deps import get_playback_service

router = APIRouter(prefix="/api/items", tags=["streaming"])


@router.get("/{media_id}/stream")
async def stream_item(
    media_id: str,
    request: Request,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    return await playback.stream(media_id, request)


@router.get("/{media_id}/hls/master.m3u8")
def hls_master(
    media_id: str,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    return playback.hls_master(media_id)


@router.get("/{media_id}/hls/{asset:path}")
def hls_asset(
    media_id: str,
    asset: str,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    return playback.hls_asset(media_id, asset)


@router.get("/{media_id}/live/{asset:path}")
async def live_asset(
    media_id: str,
    asset: str,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    try:
        return await playback.live_asset(media_id, asset)
    except Exception as exc:
        from app.utils.logging import logger
        logger.exception("live_asset error: {}", exc)
        raise


@router.get("/{media_id}/artwork/{name}")
def get_artwork(
    media_id: str,
    name: str,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    return playback.artwork(media_id, name)


@router.get("/{media_id}/subtitles")
def list_subtitles(
    media_id: str,
    playback: PlaybackService = Depends(get_playback_service),
) -> list[dict] | None:
    tracks = playback.subtitle_tracks(media_id)
    if tracks is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return tracks


@router.get("/{media_id}/subtitles/{index}")
def get_subtitle(
    media_id: str,
    index: int,
    playback: PlaybackService = Depends(get_playback_service),
) -> Response:
    response = playback.subtitle_file(media_id, index)
    if response is None:
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return response