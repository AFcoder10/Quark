from __future__ import annotations

import asyncio
import subprocess
import threading
from collections import deque
from pathlib import Path

from loguru import logger


class FFmpegProcessError(Exception):
    pass


class FFmpegRunner:
    def __init__(self, args: list[str], *, cwd: Path | None = None, log_tag: str = "ffmpeg") -> None:
        self.args = args
        self.cwd = cwd
        self.log_tag = log_tag
        self.process: subprocess.Popen | None = None
        self._stderr_thread: threading.Thread | None = None
        self._error_tail: str | None = None
        self._started = False

    async def start(self) -> None:
        self.process = await asyncio.to_thread(
            subprocess.Popen,
            self.args,
            cwd=str(self.cwd) if self.cwd else None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        self._started = True
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

    def _drain_stderr(self) -> None:
        if self.process is None or self.process.stderr is None:
            return
        tail: deque[str] = deque(maxlen=5)
        try:
            for raw_line in self.process.stderr:
                text = raw_line.decode(errors="replace").rstrip()
                if text:
                    tail.append(text)
        except Exception:
            pass
        if tail:
            self._error_tail = " | ".join(tail)

    async def wait(self) -> int:
        if self.process is None:
            raise FFmpegProcessError("Process not started")
        return await asyncio.to_thread(self.process.wait)

    async def run(self) -> None:
        await self.start()
        return_code = await self.wait()
        if return_code != 0:
            detail = f" (stderr: {self._error_tail})" if self._error_tail else ""
            raise FFmpegProcessError(f"{self.log_tag} exited with code {return_code}{detail}")

    async def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        try:
            self.process.kill()
            await asyncio.to_thread(self.process.wait)
        except Exception:
            pass
        if self._stderr_thread is not None:
            try:
                if self.process.stderr is not None:
                    self.process.stderr.close()
            except Exception:
                pass
        logger.debug("Stopped {} process", self.log_tag)
