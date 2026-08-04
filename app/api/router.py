from __future__ import annotations

from app.api.deps import get_index
from app.api.routes import items, libraries, optimization, shows, state, streaming, system
from app.config.settings import settings
from app.utils.logging import setup_logger

from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(libraries.router)
api_router.include_router(items.router)
api_router.include_router(streaming.router)
api_router.include_router(optimization.router)
api_router.include_router(state.router)
api_router.include_router(shows.router)