from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


def dumps(data: Any) -> str:
    return orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode()


def loads(text: str) -> Any:
    return orjson.loads(text)


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return orjson.loads(path.read_bytes())
    except (OSError, ValueError):
        return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    tmp.replace(path)