from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.filenames import parse_episode, parse_episode_number, parse_season_from_dir


class TestParseEpisodeNumber:
    def test_ep1(self):
        assert parse_episode_number("ep1.mp4") == 1

    def test_EP02(self):
        assert parse_episode_number("EP02") == 2

    def test_episode01(self):
        assert parse_episode_number("episode01") == 1

    def test_ep5_720p(self):
        assert parse_episode_number("ep5.720p.WEB-DL") == 5

    def test_ep12(self):
        assert parse_episode_number("ep12") == 12

    def test_no_match(self):
        assert parse_episode_number("Pilot.mp4") is None

    def test_renamed_01x01(self):
        assert parse_episode_number("01x01 - Pilot.mp4") is None

    def test_no_ep_within(self):
        assert parse_episode_number("hello world") is None


class TestParseSeasonDir:
    def test_season_01(self):
        assert parse_season_from_dir("Season 01") == 1

    def test_season_10(self):
        assert parse_season_from_dir("Season 10") == 10

    def test_s01(self):
        assert parse_season_from_dir("S01") == 1

    def test_s2(self):
        assert parse_season_from_dir("S2") == 2

    def test_season_01_underscore(self):
        assert parse_season_from_dir("season_01") == 1

    def test_not_season(self):
        assert parse_season_from_dir("Extras") is None

    def test_show_name(self):
        assert parse_season_from_dir("Breaking Bad") is None


class TestParseEpisodeRenamed:
    def test_01x01_pilot(self):
        assert parse_episode("01x01 - Pilot") == (1, 1)

    def test_01x02(self):
        assert parse_episode("01x02 - Cats in the Bag") == (1, 2)

    def test_02x01(self):
        assert parse_episode("02x01 - Seven Thirty-Seven") == (2, 1)
