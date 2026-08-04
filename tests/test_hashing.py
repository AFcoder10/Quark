from __future__ import annotations

from pathlib import Path

from app.utils.hashing import file_id_for, media_id_for, sha1_hex


class TestSha1Hex:
    def test_consistent(self):
        assert sha1_hex("hello") == sha1_hex("hello")

    def test_different(self):
        assert sha1_hex("hello") != sha1_hex("world")

    def test_length(self):
        assert len(sha1_hex("test")) == 40


class TestFileIdFor:
    def test_length(self):
        path = Path("C:/movies/test.mp4")
        assert len(file_id_for(path)) == 16

    def test_consistent(self):
        path = Path("C:/movies/test.mp4")
        assert file_id_for(path) == file_id_for(path)


class TestMediaIdFor:
    def test_movie_prefix(self):
        path = Path("C:/movies/test.mp4")
        assert media_id_for("movie", path).startswith("mv-")

    def test_episode_prefix(self):
        path = Path("C:/shows/test.mp4")
        assert media_id_for("episode", path).startswith("ep-")

    def test_length(self):
        path = Path("C:/movies/test.mp4")
        assert len(media_id_for("movie", path)) == 19  # "mv-" + 16 hex