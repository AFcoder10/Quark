from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config.settings import BASE_DIR


class _ConfigHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[], None]) -> None:
        self.on_change = on_change

    def on_modified(self, event) -> None:
        if event.src_path.endswith(".json"):
            try:
                self.on_change()
            except Exception:
                pass


class ConfigWatcher:
    def __init__(self, on_change: Callable[[], None]) -> None:
        self._observer = Observer()
        self._handler = _ConfigHandler(on_change)
        self._config_dir = BASE_DIR / "config"

    def start(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(self._handler, str(self._config_dir), recursive=False)
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)