from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field

from app.events.bus import event_bus
from app.utils.time_utils import utcnow_iso


@dataclass
class JobState:
    media_id: str
    status: str = "queued"
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    created_at: str = field(default_factory=utcnow_iso)
    finished_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class OptimizationQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, JobState] = {}

    def enqueue(self, media_id: str) -> bool:
        current = self._jobs.get(media_id)
        if current is not None and current.status in ("queued", "running"):
            return False
        self._jobs[media_id] = JobState(media_id=media_id)
        self._queue.put_nowait(media_id)
        event_bus.publish("optimize.queued", media_id=media_id)
        return True

    async def next(self) -> str:
        return await self._queue.get()

    def start(self, media_id: str) -> None:
        job = self._jobs.get(media_id)
        if job is not None:
            job.status = "running"
            job.progress = 0.0
        event_bus.publish("optimize.started", media_id=media_id)

    def update(self, media_id: str, progress: float, message: str) -> None:
        job = self._jobs.get(media_id)
        if job is not None:
            job.progress = round(progress, 3)
            job.message = message
        event_bus.publish("optimize.progress", media_id=media_id, progress=progress, message=message)

    def finish(self, media_id: str) -> None:
        job = self._jobs.get(media_id)
        if job is not None:
            job.status = "done"
            job.progress = 1.0
            job.message = "Optimization complete"
            job.finished_at = utcnow_iso()
        event_bus.publish("optimize.completed", media_id=media_id)

    def fail(self, media_id: str, error: str) -> None:
        job = self._jobs.get(media_id)
        if job is not None:
            job.status = "failed"
            job.error = error
            job.finished_at = utcnow_iso()
        event_bus.publish("optimize.failed", media_id=media_id, error=error)

    def cancel(self, media_id: str) -> bool:
        job = self._jobs.get(media_id)
        if job is None or job.status in ("done", "failed"):
            return False
        job.status = "cancelled"
        job.finished_at = utcnow_iso()
        event_bus.publish("optimize.cancelled", media_id=media_id)
        return True

    def should_cancel(self, media_id: str) -> bool:
        job = self._jobs.get(media_id)
        return bool(job is not None and job.status == "cancelled")

    def status(self, media_id: str) -> dict | None:
        job = self._jobs.get(media_id)
        return job.to_dict() if job is not None else None

    def all(self) -> list[dict]:
        return [job.to_dict() for job in self._jobs.values()]