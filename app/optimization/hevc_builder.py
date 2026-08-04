from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from app.cache.manager import cache
from app.metadata.models import Metadata
from app.system.commands import FFMPEG, require_binary
from app.transcoding.ffmpeg import FFmpegRunner


class HEVCOptimizationError(Exception):
    pass


class HEVCBuilder:
    def __init__(self, on_progress: Callable[[float, str], None] | None = None) -> None:
        self.on_progress = on_progress

    def _progress(self, fraction: float, message: str) -> None:
        if self.on_progress is not None:
            self.on_progress(fraction, message)

    async def build(self, meta: Metadata) -> Metadata:
        require_binary(FFMPEG)
        media_id = meta.media_id
        primary = Path(meta.primary_file)
        if not primary.exists():
            raise HEVCOptimizationError(f"Media file not found: {primary}")

        out_dir = cache.optimized_dir(media_id)
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        output_file = out_dir / "hevc.mp4"

        cmd = [
            require_binary(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(primary),
            "-c:v",
            "libx265",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-ac",
            "2",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_file),
        ]

        duration = meta.files[0].duration if meta.files and meta.files[0].duration else 0.0

        def on_time(parsed_time: float) -> None:
            if duration > 0:
                pct = min(1.0, max(0.0, parsed_time / duration))
                self._progress(pct, f"Encoding HEVC ({int(pct * 100)}%)")

        runner = FFmpegRunner(on_progress=on_time)
        await runner.run(cmd)

        meta.optimization.status = "done"
        meta.optimization.enabled = True
        meta.optimization.path = str(out_dir)
        meta.optimization.progress = 1.0

        return meta
