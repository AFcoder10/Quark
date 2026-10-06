from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def lib_repo(tmp_path, monkeypatch):
    import app.db.repositories as repo

    test_db = repo.db.__class__(tmp_path / "lib.db")
    monkeypatch.setattr(repo, "db", test_db)
    yield repo.libraries
    test_db.close()


def test_library_crud(lib_repo):
    assert lib_repo.all() == []
    lib_repo.upsert({"id": "a1", "name": "Movies", "path": "/m", "type": "movie", "enabled": True})
    rows = lib_repo.all()
    assert len(rows) == 1 and rows[0]["name"] == "Movies"
    assert rows[0]["enabled"] is True

    lib_repo.upsert({"id": "a1", "name": "Films", "path": "/m", "type": "movie", "enabled": False})
    assert lib_repo.all()[0]["name"] == "Films"
    assert lib_repo.all()[0]["enabled"] is False

    assert lib_repo.delete("a1") is True
    assert lib_repo.all() == []
    assert lib_repo.delete("missing") is False


def test_library_persisted_in_sqlite(tmp_path):
    from app.db.database import Database
    from app.db.repositories import LibraryRepository

    db_path = tmp_path / "persist.db"
    db1 = Database(db_path)
    from app.db import repositories as repo

    class Repo1(LibraryRepository):
        pass

    original = repo.db
    repo.db = db1
    try:
        repo.libraries.upsert({"id": "x", "name": "Music", "path": "/music", "type": "music", "enabled": True})
    finally:
        repo.db = original

    # reopen with a fresh connection: data must survive
    db2 = Database(db_path)
    repo.db = db2
    try:
        rows = repo.libraries.all()
        assert len(rows) == 1 and rows[0]["type"] == "music"
    finally:
        repo.db = original
