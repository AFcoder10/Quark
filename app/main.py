from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager, suppress

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.cache.manager import cache
from app.config.libraries import libraries
from app.config.settings import BASE_DIR, settings
from app.events.bus import event_bus
from app.optimization.queue import OptimizationQueue
from app.optimization.worker import optimization_worker
from app.scanner.index import LibraryIndex
from app.scanner.scanner import LibraryScanner
from app.services.library_service import LibraryService
from app.services.playback_service import PlaybackService
from app.streaming.live import LiveTranscodeManager
from app.streaming.manager import PlaybackManager
from app.system.state import StateStore
from app.system.watcher import ConfigWatcher
from app.utils.logging import setup_logger
from app.websocket.manager import manager
from app.workers.scanner_worker import ScanManager

UI_DIST = BASE_DIR / "web" / "dist"


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.load()
        libraries.load()
        cache.ensure()
        setup_logger(BASE_DIR / "logs", settings.data.server.log_level)

        from app.db.database import db
        from app.db.migration import maybe_migrate

        db.connect()
        maybe_migrate()

        index = LibraryIndex(cache.index_file)
        index.load()

        scanner = LibraryScanner(index)
        scan_manager = ScanManager(scanner)
        queue = OptimizationQueue()
        live = LiveTranscodeManager()
        playback = PlaybackManager(live)
        state_store = StateStore(cache.state_file)

        app.state.index = index
        app.state.library_service = LibraryService(scanner, index)
        app.state.playback_service = PlaybackService(playback)
        app.state.optimization_queue = queue
        app.state.scan_manager = scan_manager
        app.state.state_store = state_store

        event_bus.on_any(manager.publish_event)

        watcher = ConfigWatcher(lambda: (settings.reload(), libraries.load()))
        watcher.start()

        await live.start()
        worker_task = asyncio.create_task(optimization_worker(queue))

        from app.utils.logging import logger

        logger.info("Quark backend started (host={}, port={})", settings.data.server.host, settings.data.server.port)

        try:
            yield
        finally:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task
            await live.stop()
            watcher.stop()
            from app.providers import close_providers
            await close_providers()

    app = FastAPI(title="Quark", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    if UI_DIST.is_dir():
        app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def ui_fallback(full_path: str):
            candidate = UI_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(UI_DIST / "index.html")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app


app = create_app()
