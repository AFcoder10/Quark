from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from app.config.settings import BASE_DIR

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS items (
    media_id      TEXT PRIMARY KEY,
    kind          TEXT NOT NULL,
    library_id    TEXT NOT NULL,
    title         TEXT NOT NULL,
    series_title  TEXT,
    season        INTEGER,
    episode       INTEGER,
    year          INTEGER,
    display_title TEXT NOT NULL,
    data          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_library ON items(library_id);
CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind);
CREATE INDEX IF NOT EXISTS idx_items_series ON items(series_title);

CREATE TABLE IF NOT EXISTS metadata (
    media_id    TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    library_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    updated_at  TEXT,
    data        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metadata_kind ON metadata(kind);
CREATE INDEX IF NOT EXISTS idx_metadata_library ON metadata(library_id);

CREATE TABLE IF NOT EXISTS playback_state (
    media_id       TEXT PRIMARY KEY,
    position       REAL DEFAULT 0,
    duration       REAL DEFAULT 0,
    watched        INTEGER DEFAULT 0,
    last_played_at TEXT
);

CREATE TABLE IF NOT EXISTS optimization_jobs (
    media_id    TEXT PRIMARY KEY,
    mode        TEXT NOT NULL DEFAULT 'hls',
    status      TEXT NOT NULL,
    progress    REAL DEFAULT 0,
    message     TEXT DEFAULT '',
    error       TEXT,
    created_at  TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS libraries (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    path    TEXT NOT NULL,
    type    TEXT NOT NULL DEFAULT 'movie',
    enabled INTEGER NOT NULL DEFAULT 1
);
"""


class Database:
    """Thin, thread-safe SQLite wrapper (WAL mode).

    A single connection guarded by a lock keeps things simple and safe for a
    local, single-user server. FastAPI runs sync endpoints in a threadpool and
    background workers touch the DB from other threads, so access is locked.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else BASE_DIR / "cache" / "quark.db"
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        with self._lock:
            if self._conn is None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(self.path), check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.executescript(_SCHEMA)
                conn.execute(
                    "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
                conn.commit()
                self._conn = conn
            return self._conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            conn = self.connect()
            cur = conn.execute(sql, params)
            conn.commit()
            return cur

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            conn = self.connect()
            return list(conn.execute(sql, params).fetchall())

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            conn = self.connect()
            return conn.execute(sql, params).fetchone()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


db = Database()
