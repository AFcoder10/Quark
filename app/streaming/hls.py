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


def _video_codecs(meta: Metadata) -> str:
    codec = (meta.video.codec or "h264").lower() if meta.video else "h264"
    if codec == "h264":
        return "avc1.640029"
    if codec == "hevc":
        return "hev1.1.6.L120.B0"
    return "avc1.640029"


def _audio_codecs(meta: Metadata) -> str:
    if meta.audio and meta.audio[0].codec:
        codec = meta.audio[0].codec.lower()
        if codec == "aac":
            return "mp4a.40.2"
        if codec in ("ac3", "eac3", "ec-3"):
            return "ec-3"
    return "mp4a.40.2"


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

    codecs = _video_codecs(meta)
    if has_audio:
        codecs = f"{codecs},{_audio_codecs(meta)}"

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