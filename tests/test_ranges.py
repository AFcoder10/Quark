from __future__ import annotations

import pytest

from app.streaming.ranges import parse_range_header


class TestParseRangeHeader:
    def test_none_header(self):
        assert parse_range_header(None, 1000) is None

    def test_empty_string(self):
        assert parse_range_header("", 1000) is None

    def test_invalid_prefix(self):
        assert parse_range_header("invalid", 1000) is None

    def test_full_range(self):
        result = parse_range_header("bytes=0-999", 1000)
        assert result == [(0, 999)]

    def test_open_ended(self):
        result = parse_range_header("bytes=500-", 1000)
        assert result == [(500, 999)]

    def test_suffix_range(self):
        result = parse_range_header("bytes=-200", 1000)
        assert result == [(800, 999)]

    def test_multiple_ranges(self):
        result = parse_range_header("bytes=0-499,500-999", 1000)
        assert result == [(0, 499), (500, 999)]

    def test_clamp_end(self):
        result = parse_range_header("bytes=0-9999", 1000)
        assert result == [(0, 999)]

    def test_start_beyond_size(self):
        result = parse_range_header("bytes=1000-1999", 1000)
        assert result == []

    def test_invalid_range(self):
        result = parse_range_header("bytes=abc-def", 1000)
        assert result == []

    def test_sorted(self):
        result = parse_range_header("bytes=500-999,0-499", 1000)
        assert result == [(0, 499), (500, 999)]