from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import Database
from app.media.kinds import MediaKind
from app.media.models import MediaFile, MediaItem
from app.metadata.models import Metadata
from app.utils.time_utils import utcnow_iso


@pytest.fixture()
def repos(tmp_path, monkeypatch):
    import app.db.repositories as repo
    from app.db.database import Database as _DB

    test_db = _DB(tmp_path / "test.db")
    monkeypatch.setattr(repo, "db", test_db)
    repo.items._cache = None
    yield repo
    test_db.close()


def test_schema_tables(tmp_path):
    database = Database(tmp_path / "t.db")
    tables = {row["name"] for row in database.query("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"items", "metadata", "playback_state", "optimization_jobs", "settings"} <= tables
    database.close()


def test_item_roundtrip_and_kind_equality(repos):
    item = MediaItem(
        media_id="mv-1",
        kind=MediaKind.MOVIE,
        library_id="lib1",
        title="Matrix",
        year=1999,
        files=[MediaFile(path="/m/a.mp4", size=10, extension="mp4")],
        primary_file="/m/a.mp4",
    )
    repos.items.upsert(item)
    got = repos.items.get("mv-1")
    assert got is not None
    assert got.title == "Matrix"
    assert got.kind == "movie"  # str-enum equality preserved
    assert got.display_title == "Matrix (1999)"


def test_items_query_helpers(repos):
    repos.items.upsert(MediaItem(media_id="mv-1", library_id="L1", title="M", primary_file="/m"))
    repos.items.upsert(
        MediaItem(
            media_id="ep-1",
            kind=MediaKind.EPISODE,
            library_id="L2",
            title="Pilot",
            series_title="Breaking Bad",
            season=1,
            episode=1,
            primary_file="/e",
        )
    )
    assert len(repos.items.by_library("L1")) == 1
    assert [e.media_id for e in repos.items.by_series("Breaking Bad")] == ["ep-1"]
    assert repos.items.remove("ep-1") is True
    assert repos.items.count() == 1


def test_metadata_roundtrip(repos):
    meta = Metadata(media_id="mv-1", kind=MediaKind.MOVIE, library_id="L", title="The Matrix", tmdb_id=603)
    repos.metadata.upsert(meta)
    got = repos.metadata.get("mv-1")
    assert got is not None and got.title == "The Matrix" and got.tmdb_id == 603
    repos.metadata.delete("mv-1")
    assert repos.metadata.get("mv-1") is None


def test_state_upsert_and_all(repos):
    repos.state.update("mv-1", position=42.5, duration=100.0, watched=False)
    state = repos.state.get("mv-1")
    assert state["position"] == 42.5
    assert state["watched"] is False
    assert "mv-1" in repos.state.all()


def test_jobs_roundtrip(repos):
    repos.jobs.upsert({"media_id": "mv-1", "mode": "hls", "status": "done", "progress": 1.0, "message": "ok"})
    jobs = repos.jobs.all()
    assert len(jobs) == 1 and jobs[0]["status"] == "done"


def test_schema_version_recorded(tmp_path):
    database = Database(tmp_path / "t.db")
    row = database.query_one("SELECT value FROM meta WHERE key='schema_version'")
    assert row is not None and row["value"] == "1"
    database.close()
