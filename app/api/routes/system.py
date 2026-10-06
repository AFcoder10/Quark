from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.libraries import libraries
from app.config.settings import settings
from app.scanner.index import LibraryIndex
from app.system import commands
from app.system.platform import platform_name
from app.api.deps import get_index

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/browse")
def browse(path: str | None = None) -> dict:
    """List directories under `path` so the UI can offer a folder picker.

    Local, single-user server: browsing the filesystem is expected (as in
    Jellyfin/Plex setup). Directories only — files are not returned.
    """
    base = Path(path).expanduser() if path else Path.home()
    try:
        base = base.resolve()
    except OSError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not base.exists() or not base.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {base}")

    entries = []
    try:
        for child in sorted(base.iterdir(), key=lambda p: p.name.lower()):
            if child.name.startswith("."):
                continue
            try:
                if child.is_dir():
                    entries.append({"name": child.name, "path": str(child)})
            except OSError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {base}")

    parent = str(base.parent) if base.parent != base else None
    return {
        "path": str(base),
        "parent": parent,
        "home": str(Path.home()),
        "entries": entries,
    }



@router.get("/health")
async def health(index: LibraryIndex = Depends(get_index)) -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "platform": platform_name(),
        "ffmpeg": commands.find_binary("ffmpeg") is not None,
        "ffprobe": commands.find_binary("ffprobe") is not None,
        "mediainfo": commands.find_binary("mediainfo") is not None,
        "libraries": len(libraries.all()),
        "items": len(index),
    }


@router.get("/settings")
def get_settings(request: Request) -> dict:
    data = settings.data.model_dump(mode="json")
    providers = data.get("providers", {})
    for key, value in providers.items():
        if isinstance(value, dict):
            for secret in ("api_key", "password", "api-key"):
                if secret in value and value[secret]:
                    value[secret] = "***"
    return data


@router.post("/settings/reload")
def reload_settings() -> dict:
    from app.config.libraries import libraries

    settings.reload()
    libraries.load()
    return {"status": "ok"}


@router.put("/settings")
def update_settings(body: dict) -> dict:
    current = settings.data.model_dump(mode="json")
    for key in ("server", "streaming", "optimization", "providers"):
        if key in body and isinstance(body[key], dict):
            merged = dict(current.get(key, {}))
            for k, v in body[key].items():
                if isinstance(v, dict):
                    nested = dict(merged.get(k, {})) if isinstance(merged.get(k), dict) else {}
                    for nk, nv in v.items():
                        if nk in ("api_key", "password", "api-key") and nv == "***":
                            continue
                        nested[nk] = nv
                    merged[k] = nested
                else:
                    merged[k] = v
            current[key] = merged
    settings.update(current)
    return {"status": "ok", **settings.data.model_dump(mode="json")}


@router.post("/restart")
async def restart_server() -> dict:
    """Signal the main.py supervisor to close & reopen the backend terminal."""
    from app.config.settings import BASE_DIR

    marker = BASE_DIR / ".restart_request"
    try:
        marker.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "restarting", "time": datetime.now(timezone.utc).isoformat()}