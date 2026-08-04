# Quark Backend Architecture (Python 3.12.10)

## Purpose

Quark is a self-hosted media streaming server focused on:

-   Original quality playback (HTTP Byte Range)
-   Adaptive HLS streaming
-   Offline optimization
-   Rich metadata
-   Beautiful artwork
-   Cross-platform support (Windows + Linux Mint)
-   Simple JSON-based metadata storage

------------------------------------------------------------------------

# Technology Stack

  Component    Technology
  ------------ ------------------------------
  Language     Python 3.12.10
  API          FastAPI
  Server       Uvicorn
  Media        FFmpeg + FFprobe + MediaInfo
  Metadata     TMDB
  Artwork      FanArt.tv + TMDB
  Subtitles    OpenSubtitles
  Storage      JSON
  Async HTTP   httpx
  Validation   Pydantic v2
  Streaming    HTTP Byte Range + HLS

------------------------------------------------------------------------

# High-Level Rules (For Any LLM Working On Quark)

## General Rules

-   Keep modules small and focused.
-   Do not mix business logic into API routes.
-   Use async whenever practical.
-   Never duplicate logic.
-   Keep platform-specific code inside `app/system/`.
-   Use pathlib instead of string paths.
-   Use JSON metadata; do not introduce SQL unless explicitly requested.

## Streaming Rules

1.  Prefer Direct Play (HTTP Byte Range).
2.  If an optimized HLS cache exists, serve it.
3.  If neither is possible, perform live HLS transcoding.
4.  Never modify the original media while streaming.

## Metadata Rules

Every movie or episode must have one `metadata.json` containing:

-   IDs (TMDB, IMDb, UUID)
-   File information
-   Video information
-   Audio tracks
-   Subtitle tracks
-   Chapters
-   Artwork
-   Optimization status
-   Playback information
-   Timestamps

Always build metadata using:

-   FFprobe
-   MediaInfo
-   TMDB
-   FanArt.tv
-   OpenSubtitles

## Artwork Rules

Download assets once and cache them locally.

Prefer:

1.  FanArt.tv
2.  TMDB

Cache:

-   Posters
-   Backdrops
-   Logos
-   Clear Logos
-   ClearArt
-   DiscArt
-   Banners
-   Landscapes
-   Thumbnails

Never rely on remote URLs during playback.

## Subtitle Rules

-   Read embedded subtitles.
-   Download external subtitles from OpenSubtitles.
-   Cache locally.
-   Match using TMDB/IMDb identifiers instead of filenames.

## Optimization Rules

Optimization is optional.

When requested:

-   Read metadata.
-   Generate HLS renditions (2160p, 1440p, 1080p, 720p, 480p, 360p,
    240p, 144p where applicable).
-   Preserve all compatible audio tracks.
-   Generate subtitle playlists.
-   Store outputs under `cache/optimized/<media_id>/`.
-   Update `metadata.json`.

## Project Structure

``` text
quark/
├── app/
│   ├── api/
│   ├── scanner/
│   ├── metadata/
│   ├── artwork/
│   ├── subtitles/
│   ├── media/
│   ├── streaming/
│   ├── optimization/
│   ├── transcoding/
│   ├── providers/
│   ├── services/
│   ├── workers/
│   ├── cache/
│   ├── config/
│   ├── system/
│   ├── utils/
│   ├── websocket/
│   ├── events/
│   └── main.py
├── media/
├── cache/
├── config/
├── docs/
├── logs/
├── tests/
├── requirements/
├── requirements.txt
├── pyproject.toml
└── run.py
```

## Processing Pipeline

``` text
Scan Library
    ↓
FFprobe + MediaInfo
    ↓
TMDB Match
    ↓
Artwork Download
    ↓
Subtitle Download
    ↓
metadata.json
    ↓
Ready to Stream
```

## Playback Pipeline

``` text
User presses Play
        │
        ▼
Read metadata.json
        │
        ▼
Optimized Cache Exists?
   ├── Yes → Serve HLS
   └── No
         │
         ▼
Direct Play Supported?
   ├── Yes → HTTP Byte Range
   └── No → Live HLS Transcode
```

## Python Environment Setup

### Windows (PowerShell)

``` powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux Mint / Ubuntu

``` bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Suggested requirements.txt

``` text
fastapi
uvicorn[standard]
httpx
aiofiles
pydantic>=2
loguru
watchdog
python-multipart
orjson
mediainfo
ffmpeg-python
```

## External Dependencies

Install separately:

-   FFmpeg (includes FFprobe)
-   MediaInfo CLI

Ensure both are available on PATH.

## Development Workflow

1.  Create a virtual environment.
2.  Activate it.
3.  Install requirements.
4.  Configure API keys in `config/settings.json`.
5.  Add media libraries in `config/libraries.json`.
6.  Run the server.
7.  Scan the library.
8.  Generate metadata.
9.  Stream or optimize media.

## Initial Development Order

1.  Configuration
2.  Scanner
3.  Metadata Builder
4.  TMDB Provider
5.  FanArt Provider
6.  OpenSubtitles Provider
7.  HTTP Byte Range Streaming
8.  HLS Streaming
9.  Optimization Queue
10. REST API
11. UI Integration
