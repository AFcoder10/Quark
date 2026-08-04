from __future__ import annotations

import hashlib
from pathlib import Path


def sha1_hex(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8", errors="surrogatepass")
    return hashlib.sha1(value).hexdigest()


def file_id_for(path: Path) -> str:
    return sha1_hex(str(path.resolve()))[:16]


def media_id_for(kind: str, path: Path) -> str:
    prefix = "mv" if kind == "movie" else "ep"
    return f"{prefix}-{file_id_for(path)}"