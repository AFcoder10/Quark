from __future__ import annotations

import asyncio
import inspect
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

from loguru import logger

Handler = Callable[..., Any]


@dataclass
class Event:
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._any_handlers: list[Handler] = []

    def on(self, name: str, handler: Handler) -> None:
        self._handlers[name].append(handler)

    def on_any(self, handler: Handler) -> None:
        self._any_handlers.append(handler)

    def publish(self, name: str, **data: Any) -> None:
        event = Event(name=name, data=data)
        for handler in self._handlers.get(name, []):
            self._dispatch(handler, event)
        for handler in self._any_handlers:
            self._dispatch(handler, event)

    @staticmethod
    def _dispatch(handler: Handler, event: Event) -> None:
        try:
            result = handler(event)
            if inspect.isawaitable(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(result)
                        else:
                            result.close()
                    except RuntimeError:
                        result.close()
        except Exception:
            logger.exception("Event handler failed for {}", event.name)


event_bus = EventBus()