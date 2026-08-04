from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass, field

from app.config.libraries import libraries
from app.events.bus import event_bus
from app.scanner.scanner import LibraryScanner
from app.utils.time_utils import utcnow_iso


@dataclass
class ScanJob:
    job_id: str
    library_id: str
    status: str = "queued"
    error: str | None = None
    result: dict = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow_iso)
    finished_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ScanManager:
    def __init__(self, scanner: LibraryScanner) -> None:
        self.scanner = scanner
        self._jobs: dict[str, ScanJob] = {}

    async def start(self, library_id: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = ScanJob(job_id=job_id, library_id=library_id)
        asyncio.create_task(self._run(job_id, library_id))
        return job_id

    async def scan_all(self) -> None:
        for library in libraries.all():
            if library.enabled:
                await self.start(library.id)

    async def _run(self, job_id: str, library_id: str) -> None:
        job = self._jobs[job_id]
        job.status = "running"
        try:
            library = libraries.get(library_id)
            if library is None:
                raise ValueError(f"Library not found: {library_id}")
            result = await self.scanner.scan_library(library)
            job.status = "done"
            job.result = {"added": result.added, "removed": result.removed}
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
        finally:
            job.finished_at = utcnow_iso()
            event_bus.publish("scan.job_finished", job_id=job_id, library_id=library_id, status=job.status)

    def status(self, job_id: str) -> dict | None:
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None

    def all(self) -> list[dict]:
        return [job.to_dict() for job in self._jobs.values()]