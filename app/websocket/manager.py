from __future__ import annotations

from typing import Any

from fastapi import WebSocket

from app.events.bus import Event
from app.utils.json_utils import dumps


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        for websocket in list(self._connections):
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(websocket)

    async def publish_event(self, event: Event) -> None:
        payload: str = dumps({"type": event.name, "data": event.data, "ts": event.ts})
        await self.broadcast(payload)


manager = ConnectionManager()