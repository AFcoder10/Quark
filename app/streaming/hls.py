from __future__ import annotations

import mimetypes
from pathlib import Path

from app.metadata.models import AudioPlaylistInfo, Metadata, RenditionInfo, SubtitlePlaylistInfo

HLS_MEDIA_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".vtt": "text/vtt",
    ".m4s": "video/iso.segment",
    ".mp4": "video/mp4",
    ".aac": "audio/aac",
}


def hls_media_type(name: str) -> str:
    ext = Path(name).suffix.lower()
    if ext in HLS_MEDIA_TYPES:
        return HLS_MEDIA_TYPES[ext]
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


def _rendition_codecs(audio_playlists: list[AudioPlaylistInfo]) -> str:
    # Optimization renditions are always encoded with libx264.
    codecs = ["avc1.640029"]
    audio_codes: set[str] = set()
    for track in audio_playlists:
        codec = (track.codec or "aac").lower()
        if codec in ("ac3", "eac3", "ec-3"):
            audio_codes.add("ec-3")
        elif codec == "aac":
            audio_codes.add("mp4a.40.2")
    codecs.extend(sorted(audio_codes))
    return ",".join(codecs)


def build_master_playlist(
    meta: Metadata,
    renditions: list[RenditionInfo],
    audio_playlists: list[AudioPlaylistInfo],
    subtitle_playlists: list[SubtitlePlaylistInfo],
) -> str:
    lines = ["#EXTM3U", "#EXT-X-VERSION:6"]
    has_audio = bool(audio_playlists)
    has_subtitles = bool(subtitle_playlists)

    if has_audio:
        for position, track in enumerate(audio_playlists):
            default = "YES" if position == 0 else "NO"
            autoselect = "YES" if position == 0 else "NO"
            lines.append(
                f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="{track.title}",'
                f'LANGUAGE="{track.language}",DEFAULT={default},AUTOSELECT={autoselect},URI="{track.playlist}"'
            )
    if has_subtitles:
        for track in subtitle_playlists:
            forced = "YES" if track.forced else "NO"
            lines.append(
                f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{track.title}",'
                f'LANGUAGE="{track.language}",FORCED={forced},DEFAULT=NO,URI="{track.playlist}"'
            )

    codecs = _rendition_codecs(audio_playlists)

    for rendition in sorted(renditions, key=lambda item: item.height):
        attrs = [
            f"BANDWIDTH={rendition.bitrate * 1000}",
            f"AVERAGE-BANDWIDTH={int(rendition.bitrate * 0.8 * 1000)}",
            f"RESOLUTION={rendition.width}x{rendition.height}",
            f'CODECS="{codecs}"',
        ]
        if has_audio:
            attrs.append('AUDIO="audio"')
        if has_subtitles:
            attrs.append('SUBTITLES="subs"')
        lines.append("#EXT-X-STREAM-INF:" + ",".join(attrs))
        lines.append(rendition.playlist)

    return "\n".join(lines) + "\n"