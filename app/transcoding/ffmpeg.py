from __future__ import annotations

import asyncio
import subprocess
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
        self.process: asyncio.subprocess.Process | None = None
        self._stderr_task: asyncio.Task | None = None
        self._error_tail: str | None = None

    async def start(self) -> None:
        self.process = await asyncio.create_subprocess_exec(
            *self.args,
            cwd=str(self.cwd) if self.cwd else None,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self) -> None:
        if self.process is None or self.process.stderr is None:
            return
        tail: deque[str] = deque(maxlen=5)
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            if text:
                tail.append(text)
        if tail:
            self._error_tail = " | ".join(tail)

    async def wait(self) -> int:
        if self.process is None:
            raise FFmpegProcessError("Process not started")
        return await self.process.wait()

    async def run(self) -> None:
        await self.start()
        return_code = await self.wait()
        if self._stderr_task is not None:
            await self._stderr_task
        if return_code != 0:
            detail = f" (stderr: {self._error_tail})" if self._error_tail else ""
            raise FFmpegProcessError(f"{self.log_tag} exited with code {return_code}{detail}")

    async def stop(self) -> None:
        if self.process is None or self.process.returncode is not None:
            return
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
        if self._stderr_task is not None:
            self._stderr_task.cancel()
        logger.debug("Stopped %s process", self.log_tag)