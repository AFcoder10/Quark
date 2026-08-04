from __future__ import annotations

import re
from pathlib import Path

EPISODE_PATTERNS = [
    re.compile(r"[sS](?P<season>\d{1,2})[ .\-x]?[eE](?P<episode>\d{1,3})"),
    re.compile(r"(?P<season>\d{1,2})[xX](?P<episode>\d{1,3})"),
]

EP_NUMBER_RE = re.compile(r"(?i)(?:ep(?:isode)?|pt|part)[\s._-]*(\d{1,4})", re.IGNORECASE)

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
RESOLUTION_RE = re.compile(r"(?i)\b(2160p|1440p|1080p|720p|576p|540p|480p|360p|240p|144p)\b")
TAGS_RE = re.compile(
    r"(?i)\b(bluray|blu-?ray|web-?dl|webrip|hdtv|dvdrip|brrip|bdrip|hdrip|x264|x265|h264|h265|"
    r"hevc|avc|aac|ac3|eac3|dts|dd5\.?1|dd\+|atmos|10bit|8bit|remux|proper|repack|extended|"
    r"imax|uhd|4k|hdr|dv|mux|multi|dual|sample)\b"
)

SEASON_DIR_RE = re.compile(r"(?i)^season[\s._-]*(\d{1,2})$|^s(\d{1,2})$")


def parse_episode(stem: str) -> tuple[int, int] | None:
    for pattern in EPISODE_PATTERNS:
        match = pattern.search(stem)
        if match:
            season = int(match.group("season"))
            episode = int(match.group("episode"))
            if 0 < season <= 100 and 0 < episode <= 1000:
                return season, episode
    return None


def parse_episode_number(stem: str) -> int | None:
    match = EP_NUMBER_RE.search(stem)
    if match:
        ep = int(match.group(1))
        if 0 < ep <= 1000:
            return ep
    return None


def parse_season_from_dir(name: str) -> int | None:
    match = SEASON_DIR_RE.match(name)
    if match:
        for g in match.groups():
            if g is not None:
                return int(g)
    return None


def is_episode_file(name: str) -> bool:
    return parse_episode(Path(name).stem) is not None


def is_season_dir(name: str) -> bool:
    return bool(SEASON_DIR_RE.match(name))


def extract_year(stem: str) -> int | None:
    match = YEAR_RE.search(stem)
    return int(match.group(1)) if match else None


def strip_episode_token(stem: str) -> str:
    for pattern in EPISODE_PATTERNS:
        stem = pattern.sub(" ", stem)
    return stem


def clean_title(stem: str) -> str:
    text = stem
    text = RESOLUTION_RE.sub(" ", text)
    text = TAGS_RE.sub(" ", text)
    text = YEAR_RE.sub(" ", text)
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"[\[\](){}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text