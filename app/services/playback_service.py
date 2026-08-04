from __future__ import annotations

from fastapi import Request, Response

from app.streaming.manager import PlaybackManager


class PlaybackService:
    def __init__(self, manager: PlaybackManager) -> None:
        self.manager = manager

    async def stream(self, media_id: str, request: Request) -> Response:
        return await self.manager.stream(media_id, request)

    def hls_master(self, media_id: str) -> Response:
        return self.manager.hls_master(media_id)

    def hls_asset(self, media_id: str, asset: str) -> Response:
        return self.manager.hls_asset(media_id, asset)

    async def live_asset(self, media_id: str, asset: str) -> Response:
        return await self.manager.live_asset(media_id, asset)

    def artwork(self, media_id: str, name: str) -> Response:
        return self.manager.artwork(media_id, name)

    def subtitle_tracks(self, media_id: str) -> list[dict] | None:
        return self.manager.subtitle_tracks(media_id)

    def subtitle_file(self, media_id: str, index: int) -> Response | None:
        return self.manager.subtitle_file(media_id, index)