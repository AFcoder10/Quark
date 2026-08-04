from __future__ import annotations

import pytest

from app.utils.filenames import clean_title, extract_year, is_episode_file, is_season_dir, parse_episode


class TestParseEpisode:
    def test_s01e01(self):
        assert parse_episode("Show.S01E01.720p") == (1, 1)

    def test_s01e12(self):
        assert parse_episode("Series S01E12 HDTV") == (1, 12)

    def test_s02e03(self):
        assert parse_episode("[2023] S02E03.1080p.WEB-DL") == (2, 3)

    def test_uppercase(self):
        assert parse_episode("SHOW.S05E09") == (5, 9)

    def test_1x01_format(self):
        assert parse_episode("Show.1x01") == (1, 1)

    def test_10x03_format(self):
        assert parse_episode("Show.10x03") == (10, 3)

    def test_no_match(self):
        assert parse_episode("The.Matrix.1999.1080p") is None

    def test_short_season(self):
        assert parse_episode("S1E1") == (1, 1)

    def test_hyphenated(self):
        assert parse_episode("Show-S03E04") == (3, 4)


class TestIsEpisodeFile:
    def test_episode_file(self):
        assert is_episode_file("Show.S01E01.mp4") is True

    def test_movie_file(self):
        assert is_episode_file("The.Matrix.1999.mp4") is False


class TestExtractYear:
    def test_year(self):
        assert extract_year("Movie.2020.1080p") == 2020

    def test_no_year(self):
        assert extract_year("Movie.1080p") is None

    def test_1999(self):
        assert extract_year("Movie.1999.BluRay") == 1999


class TestIsSeasonDir:
    def test_season_dir(self):
        assert is_season_dir("Season 01") is True

    def test_s01_dir(self):
        assert is_season_dir("S01") is True

    def test_not_season_dir(self):
        assert is_season_dir("Extras") is False


class TestCleanTitle:
    def test_clean(self):
        result = clean_title("Movie.2020.1080p.BluRay.x264-GROUP")
        assert "Movie" in result
        assert "2020" not in result
        assert "1080p" not in result

    def test_underscores(self):
        result = clean_title("My_Movie_Name")
        assert "My Movie Name" in result