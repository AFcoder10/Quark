from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi.responses import StreamingResponse


def parse_range_header(header: str | None, size: int) -> list[tuple[int, int]] | None:
    if not header:
        return None
    if not header.startswith("bytes="):
        return None
    ranges: list[tuple[int, int]] = []
    for part in header.removeprefix("bytes=").split(","):
        part = part.strip()
        if not part:
            continue
        start_text, _, end_text = part.partition("-")
        try:
            if start_text == "":
                suffix = int(end_text)
                if suffix <= 0:
                    continue
                start = max(size - suffix, 0)
                end = size - 1
            else:
                start = int(start_text)
                end = int(end_text) if end_text else size - 1
        except ValueError:
            continue
        if end >= size:
            end = size - 1
        if start >= size or start > end:
            continue
        ranges.append((start, end))
    if not ranges:
        return []
    ranges.sort()
    return ranges


class RangeFileResponse(StreamingResponse):
    def __init__(
        self,
        path: Path,
        *,
        media_type: str | None = None,
        headers: dict[str, str] | None = None,
        range_header: str | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> None:
        self.path = path
        self.file_size = path.stat().st_size
        self.chunk_size = chunk_size
        headers = dict(headers or {})
        headers.setdefault("Accept-Ranges", "bytes")

        ranges = parse_range_header(range_header, self.file_size) if range_header else None
        status_code = 200
        iterator = self._iter_single((0, self.file_size - 1))

        if ranges is None:
            headers["Content-Length"] = str(self.file_size)
        elif len(ranges) == 1:
            start, end = ranges[0]
            headers["Content-Length"] = str(end - start + 1)
            headers["Content-Range"] = f"bytes {start}-{end}/{self.file_size}"
            status_code = 206
            iterator = self._iter_single((start, end))
        elif ranges:
            boundary = f"quark-{uuid4().hex}"
            headers["Content-Type"] = f"multipart/byteranges; boundary={boundary}"
            status_code = 206
            iterator = self._iter_multi(ranges, boundary)
        else:
            headers["Content-Range"] = f"bytes */{self.file_size}"
            status_code = 416
            iterator = self._iter_single((0, -1))

        if media_type is None:
            media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        super().__init__(content=iterator, status_code=status_code, media_type=media_type, headers=headers)

    async def _iter_single(self, bounds: tuple[int, int]) -> None:
        start, end = bounds
        if start < 0 or start > end or start >= self.file_size:
            return
        async with aiofiles.open(self.path, "rb") as file:
            await file.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = await file.read(min(self.chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    async def _iter_multi(self, ranges: list[tuple[int, int]], boundary: str) -> None:
        content_type = self.media_type or "application/octet-stream"
        async with aiofiles.open(self.path, "rb") as file:
            for start, end in ranges:
                yield f"--{boundary}\r\n".encode()
                yield f"Content-Type: {content_type}\r\n".encode()
                yield f"Content-Range: bytes {start}-{end}/{self.file_size}\r\n\r\n".encode()
                await file.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = await file.read(min(self.chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
                yield b"\r\n"
            yield f"--{boundary}--\r\n".encode()