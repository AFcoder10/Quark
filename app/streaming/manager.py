from __future__ import annotations

import asyncio
import mimetypes
import subprocess
from pathlib import Path

from fastapi import HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse

from app.artwork.manager import ArtworkManager
from app.cache.manager import cache
from app.config.settings import settings
from app.metadata.builder import MetadataBuilder
from app.metadata.models import Metadata
from app.streaming.live import LiveTranscodeManager
from app.streaming.ranges import RangeFileResponse
from app.system.commands import FFMPEG, require_binary


class PlaybackManager:
    def __init__(self, live: LiveTranscodeManager) -> None:
        self.live = live
        self.builder = MetadataBuilder()

    def _metadata(self, media_id: str) -> Metadata | None:
        return self.builder.load(media_id)

    async def stream(self, media_id: str, request: Request) -> Response:
        try:
            meta = self._metadata(media_id)
            if meta is None:
                raise HTTPException(status_code=404, detail="Item not found")
            mode = request.query_params.get("mode") or settings.data.streaming.default_mode
            height_param = request.query_params.get("height")
            height = int(height_param) if height_param and height_param.isdigit() else None
            start_param = request.query_params.get("start")
            start_time = float(start_param) if start_param else 0.0

            if mode == "auto":
                if self._optimized(meta):
                    mode = "hls"
                elif meta.playback.direct_play_supported:
                    mode = "direct"
                else:
                    mode = "transcode"
            if mode == "hls":
                if not self._optimized(meta):
                    mode = "transcode"
                else:
                    return RedirectResponse(f"/api/items/{media_id}/hls/master.m3u8", status_code=302)
            if mode == "direct":
                if not meta.playback.direct_play_supported:
                    mode = "transcode"
                else:
                    primary = Path(meta.primary_file)
                    if not primary.is_file():
                        raise HTTPException(status_code=404, detail="Media file missing")
                    media_type = mimetypes.guess_type(primary.name)[0] or "application/octet-stream"
                    return RangeFileResponse(
                        primary,
                        media_type=media_type,
                        range_header=request.headers.get("range"),
                    )
            if mode == "transcode":
                await self.live.ensure(media_id, meta, height=height, start_time=start_time)
                return RedirectResponse(f"/api/items/{media_id}/live/index.m3u8", status_code=302)
            raise HTTPException(status_code=400, detail=f"Unknown stream mode: {mode}")
        except Exception as exc:
            from app.utils.logging import logger
            logger.exception("Stream error: {}", exc)
            raise

    @staticmethod
    def _optimized(meta: Metadata) -> bool:
        if meta.optimization.status != "done" or not meta.optimization.path:
            return False
        return Path(meta.optimization.path, "master.m3u8").is_file()

    def hls_master(self, media_id: str) -> Response:
        meta = self._metadata(media_id)
        if meta is None or not self._optimized(meta):
            raise HTTPException(status_code=404, detail="No optimized HLS cache")
        return FileResponse(
            Path(meta.optimization.path, "master.m3u8"),
            media_type="application/vnd.apple.mpegurl",
        )

    def hls_asset(self, media_id: str, asset: str) -> Response:
        meta = self._metadata(media_id)
        if meta is None or not self._optimized(meta):
            raise HTTPException(status_code=404, detail="No optimized HLS cache")
        base = Path(meta.optimization.path).resolve()
        file = (base / asset).resolve()
        if not str(file).startswith(str(base)) or not file.is_file():
            raise HTTPException(status_code=404, detail="HLS asset not found")
        return FileResponse(file, media_type=self._guess(asset))

    async def live_asset(self, media_id: str, asset: str) -> Response:
        meta = self._metadata(media_id)
        if meta is None:
            raise HTTPException(status_code=404, detail="Item not found")
        job = self.live._jobs.get(media_id)
        if job is None or not job.running:
            try:
                await self.live.ensure(media_id, meta)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        response = self.live.serve(media_id, asset)
        if response is None:
            for _ in range(120):
                await asyncio.sleep(0.1)
                response = self.live.serve(media_id, asset)
                if response is not None:
                    break
        if response is None:
            raise HTTPException(status_code=404, detail="Live asset not ready")
        return response

    def artwork(self, media_id: str, name: str) -> Response:
        if name not in ArtworkManager.ART_TYPES:
            raise HTTPException(status_code=400, detail=f"Unknown artwork type: {name}")
        meta = self._metadata(media_id)
        if meta is None:
            raise HTTPException(status_code=404, detail="Item not found")
        path = getattr(meta.artwork, name, None)
        if not path or not Path(path).is_file():
            raise HTTPException(status_code=404, detail="Artwork not cached")
        return FileResponse(path)

    def subtitle_tracks(self, media_id: str) -> list[dict] | None:
        meta = self._metadata(media_id)
        if meta is None:
            return None
        return [track.model_dump(mode="json") for track in meta.subtitles]

    def subtitle_file(self, media_id: str, index: int) -> Response | None:
        meta = self._metadata(media_id)
        if meta is None:
            return None
        track = next((item for item in meta.subtitles if item.index == index), None)
        if track is None:
            return None

        if track.path and Path(track.path).is_file():
            return FileResponse(Path(track.path), media_type="text/vtt")

        out_vtt = cache.subtitles_dir(media_id) / f"sub_{index}.vtt"
        if out_vtt.is_file() and out_vtt.stat().st_size > 0:
            track.path = str(out_vtt)
            self.builder.save(meta)
            return FileResponse(out_vtt, media_type="text/vtt")

        primary = Path(meta.primary_file)
        if not primary.is_file():
            return None

        out_vtt.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            require_binary(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(primary),
            "-map",
            f"0:{index}",
            "-c:s",
            "webvtt",
            str(out_vtt),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and out_vtt.is_file() and out_vtt.stat().st_size > 0:
                track.path = str(out_vtt)
                self.builder.save(meta)
                return FileResponse(out_vtt, media_type="text/vtt")
        except Exception as exc:
            from app.utils.logging import logger
            logger.warning("Failed to extract subtitle track {} for {}: {}", index, media_id, exc)

        return None

    @staticmethod
    def _guess(asset: str) -> str:
        from app.streaming.hls import hls_media_type

        return hls_media_type(asset)