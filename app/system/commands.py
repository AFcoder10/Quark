from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

from app.system.platform import is_windows

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
MEDIAINFO = "mediainfo"

BINARIES: dict[str, str | None] = {FFMPEG: None, FFPROBE: None, MEDIAINFO: None}

_WINDOWS_SEARCH_PATHS = [
    Path("C:/ffmpeg/bin"),
    Path("C:/Program Files/ffmpeg/bin"),
    Path("C:/Program Files (x86)/ffmpeg/bin"),
]


def _search_windows(name: str) -> Path | None:
    if not is_windows():
        return None
    for root in _WINDOWS_SEARCH_PATHS:
        candidate = root / f"{name}.exe"
        if candidate.exists():
            return candidate
    return None


def find_binary(name: str) -> str | None:
    cached = BINARIES.get(name)
    if cached:
        return cached
    found = shutil.which(name)
    if not found:
        windows_path = _search_windows(name)
        if windows_path is not None:
            found = str(windows_path)
    if found:
        BINARIES[name] = found
    return found


def require_binary(name: str) -> str:
    found = find_binary(name)
    if not found:
        raise RuntimeError(f"Required binary '{name}' not found on PATH")
    return found


async def run_async(
    args: list[str], *, timeout: float | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    def _run() -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )

    try:
        return await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Command timed out: {args[0]}") from exc