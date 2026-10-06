from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.services.library_service import LibraryService
from app.api.deps import get_library_service, get_scan_manager
from app.workers.scanner_worker import ScanManager

router = APIRouter(prefix="/api/libraries", tags=["libraries"])


@router.get("")
def list_libraries(service: LibraryService = Depends(get_library_service)) -> list[dict]:
    result = []
    for library in service.list_libraries():
        data = library.model_dump(mode="json")
        data["path_resolved"] = str(library.resolve_path())
        result.append(data)
    return result


@router.get("/{library_id}/items-count")
def library_items_count(library_id: str, service: LibraryService = Depends(get_library_service)) -> dict:
    items = service.items(library_id=library_id)
    return {"library_id": library_id, "count": len(items)}


@router.post("", status_code=201)
def add_library(
    body: dict,
    service: LibraryService = Depends(get_library_service),
) -> dict:
    name = body.get("name")
    path = body.get("path")
    library_type = body.get("type", "movie")
    if not name or not path:
        raise HTTPException(status_code=400, detail="name and path are required")
    if library_type not in ("movie", "show", "music", "photo", "mixed"):
        raise HTTPException(status_code=400, detail="type must be one of: movie, show, music, photo, mixed")
    library = service.add_library(name=name, path=path, library_type=library_type)
    library_data = library.model_dump(mode="json")
    library_data["path_resolved"] = str(library.resolve_path())
    return library_data


@router.delete("/{library_id}")
def remove_library(library_id: str, service: LibraryService = Depends(get_library_service)) -> dict:
    if not service.remove_library(library_id):
        raise HTTPException(status_code=404, detail="Library not found")
    return {"status": "removed", "library_id": library_id}


@router.post("/scan-all", status_code=202)
async def scan_all(scan_manager: ScanManager = Depends(get_scan_manager)) -> dict:
    from app.config.libraries import libraries

    libraries_to_scan = [library.id for library in libraries.all() if library.enabled]
    if not libraries_to_scan:
        raise HTTPException(status_code=400, detail="No enabled libraries configured")
    job_ids = [await scan_manager.start(library_id) for library_id in libraries_to_scan]
    return {"status": "started", "job_ids": job_ids}


@router.post("/{library_id}/scan", status_code=202)
async def scan_library(library_id: str, scan_manager: ScanManager = Depends(get_scan_manager)) -> dict:
    from app.config.libraries import libraries

    if libraries.get(library_id) is None:
        raise HTTPException(status_code=404, detail="Library not found")
    job_id = await scan_manager.start(library_id)
    return {"status": "started", "job_id": job_id}


@router.get("/scan/jobs")
def scan_jobs(scan_manager: ScanManager = Depends(get_scan_manager)) -> dict:
    return {"jobs": scan_manager.all()}


@router.get("/scan/jobs/{job_id}")
def scan_job_status(job_id: str, scan_manager: ScanManager = Depends(get_scan_manager)) -> dict:
    status = scan_manager.status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return status