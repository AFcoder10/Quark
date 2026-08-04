from __future__ import annotations

from fastapi import Request

from app.optimization.queue import OptimizationQueue
from app.scanner.index import LibraryIndex
from app.services.library_service import LibraryService
from app.services.playback_service import PlaybackService
from app.system.state import StateStore
from app.workers.scanner_worker import ScanManager


def get_index(request: Request) -> LibraryIndex:
    return request.app.state.index


def get_library_service(request: Request) -> LibraryService:
    return request.app.state.library_service


def get_playback_service(request: Request) -> PlaybackService:
    return request.app.state.playback_service


def get_optimization_queue(request: Request) -> OptimizationQueue:
    return request.app.state.optimization_queue


def get_scan_manager(request: Request) -> ScanManager:
    return request.app.state.scan_manager


def get_state_store(request: Request) -> StateStore:
    return request.app.state.state_store