from __future__ import annotations

import asyncio
import shutil
import time
from contextlib import suppress
from pathlib import Path

from fastapi.responses import FileResponse

from app.cache.manager import cache
from app.config.settings import settings
from app.metadata.models import Metadata
from app.streaming.hls import hls_media_type
from app.system.commands import FFMPEG, require_binary
from app.transcoding.ffmpeg import FFmpegRunner


class LiveJob:
    def __init__(self, media_id: str, out_dir: Path, runner: FFmpegRunner, height: int) -> None:
        self.media_id = media_id
        self.out_dir = out_dir
        self.runner = runner
        self.height = height
        self.last_access = time.time()
        self._started = False

    def mark_started(self) -> None:
        self._started = True

    @property
    def running(self) -> bool:
        if not self._started or self.runner.process is None:
            return False
        if self.runner.process.returncode is None:
            return True
        return self.runner.process.returncode == 0 and (self.out_dir / "index.m3u8").is_file()


class LiveTranscodeManager:
    def __init__(self) -> None:
        self._jobs: dict[str, LiveJob] = {}
        self._prune_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._prune_task = asyncio.create_task(self._prune_loop())

    async def stop(self) -> None:
        if self._prune_task is not None:
            self._prune_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._prune_task
            self._prune_task = None
        for media_id in list(self._jobs):
            await self.stop_job(media_id)

    async def ensure(
        self,
        media_id: str,
        meta: Metadata,
        height: int | None = None,
        start_time: float = 0.0,
    ) -> None:
        source_height = meta.video.height if meta.video and meta.video.height else 1080
        job = self._jobs.get(media_id)
        if height is None and job is not None and job.running:
            target_height = job.height
        else:
            target_height = min(height, source_height) if height else min(settings.data.streaming.live_transcode_height, source_height)
        if job is not None and job.running and job.height == target_height and start_time <= 0.0:
            job.last_access = time.time()
            return
        if job is not None:
            await self.stop_job(media_id)
        await self._start(media_id, meta, target_height, start_time)

    async def _start(
        self,
        media_id: str,
        meta: Metadata,
        height: int,
        start_time: float = 0.0,
    ) -> None:
        primary = Path(meta.primary_file)
        if not primary.exists():
            raise ValueError(f"Media file not found: {primary}")
        out_dir = cache.live_dir(media_id)
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        segment_seconds = settings.data.optimization.segment_seconds
        source_height = meta.video.height if meta.video and meta.video.height else 1080
        copy_video = height >= source_height and bool(meta.video and (meta.video.codec or "").lower() in ("h264", "avc", "h.264"))

        cmd = [
            require_binary(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
        ]
        if start_time > 0:
            cmd.extend(["-ss", str(start_time)])
        cmd.extend([
            "-i",
            str(primary),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
        ])
        if copy_video:
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend([
                "-vf",
                f"scale=-2:{height}",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-sc_threshold",
                "0",
                "-force_key_frames",
                f"expr:gte(t,n_forced*{segment_seconds})",
            ])
        cmd.extend([
            "-c:a",
            "aac",
            "-ac",
            "2",
            "-b:a",
            "192k",
            "-hls_time",
            str(segment_seconds),
            "-hls_list_size",
            "0",
            "-hls_playlist_type",
            "event",
            "-hls_flags",
            "independent_segments",
            "-hls_segment_filename",
            str(out_dir / "seg_%06d.ts"),
            str(out_dir / "index.m3u8"),
        ])
        runner = FFmpegRunner(cmd, log_tag=f"live-{media_id}")
        await runner.start()
        job = LiveJob(media_id, out_dir, runner, height)
        job.mark_started()
        self._jobs[media_id] = job

    async def stop_job(self, media_id: str) -> None:
        job = self._jobs.pop(media_id, None)
        if job is not None and job.running:
            await job.runner.stop()

    def touch(self, media_id: str) -> None:
        job = self._jobs.get(media_id)
        if job is not None:
            job.last_access = time.time()

    def serve(self, media_id: str, asset: str) -> FileResponse | None:
        job = self._jobs.get(media_id)
        if job is None or not job.running:
            return None
        self.touch(media_id)
        file = job.out_dir / Path(asset).name
        if not file.is_file():
            return None
        return FileResponse(file, media_type=hls_media_type(asset))

    async def _prune_loop(self) -> None:
        idle_seconds = settings.data.streaming.live_idle_seconds
        while True:
            await asyncio.sleep(10)
            now = time.time()
            for media_id, job in list(self._jobs.items()):
                if not job.running:
                    await self.stop_job(media_id)
                elif now - job.last_access > idle_seconds:
                    await self.stop_job(media_id)