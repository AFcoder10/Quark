from __future__ import annotations

from pathlib import Path

from app.config.libraries import Library
from app.media.music import build_music_items, is_audio_file, read_tags
from app.media.photo import build_photo_items, is_photo_file, read_exif


def test_audio_extension_detection():
    assert is_audio_file(Path("song.mp3"))
    assert is_audio_file(Path("song.FLAC"))
    assert not is_audio_file(Path("movie.mp4")) or is_audio_file(Path("movie.mp4")) is False
    assert not is_audio_file(Path("doc.txt"))


def test_photo_extension_detection():
    assert is_photo_file(Path("a.jpg"))
    assert is_photo_file(Path("a.PNG"))
    assert is_photo_file(Path("a.cr2"))
    assert not is_photo_file(Path("a.mp4"))


def test_media_id_prefixes():
    from app.utils.hashing import media_id_for

    assert media_id_for("audio", Path("/x.mp3")).startswith("au-")
    assert media_id_for("photo", Path("/x.jpg")).startswith("ph-")
    assert media_id_for("movie", Path("/x.mp4")).startswith("mv-")
    assert media_id_for("episode", Path("/x.mp4")).startswith("ep-")


def test_build_music_items_from_tags(tmp_path: Path):
    mutagen = __import__("mutagen")
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3

    # create a tiny valid mp3 via ffmpeg if available, else skip
    import shutil
    import subprocess

    if shutil.which("ffmpeg") is None:
        return
    track = tmp_path / "track1.mp3"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=1", str(track)],
        check=True,
    )
    audio = MP3(str(track), ID3=EasyID3)
    audio["title"] = "One More Time"
    audio["artist"] = "Daft Punk"
    audio["album"] = "Discovery"
    audio["albumartist"] = "Daft Punk"
    audio["tracknumber"] = "1"
    audio.save()

    tags = read_tags(track)
    assert tags["title"] == "One More Time"
    assert tags["artist"] == "Daft Punk"
    assert tags["album"] == "Discovery"
    assert tags["track_number"] == 1

    lib = Library(id="M", name="Music", path=str(tmp_path), type="music")
    items = build_music_items(lib, tmp_path)
    assert len(items) == 1
    assert items[0].kind == "audio"
    assert items[0].album == "Discovery"
    assert items[0].media_id.startswith("au-")
    assert items[0].display_title == "01. One More Time"


def test_build_photo_items_with_exif(tmp_path: Path):
    from PIL import Image

    p = tmp_path / "beach.jpg"
    img = Image.new("RGB", (64, 48), (10, 20, 30))
    exif = Image.Exif()
    exif[272] = "Pixel 7"
    exif[271] = "Google"
    exif[36867] = "2023:07:14 18:30:00"
    img.save(p, exif=exif)

    exif_data = read_exif(p)
    assert exif_data["width"] == 64
    assert exif_data["height"] == 48
    assert exif_data["taken_at"].startswith("2023-07-14")
    assert "Google" in exif_data["camera"]

    lib = Library(id="P", name="Photos", path=str(tmp_path), type="photo")
    items = build_photo_items(lib, tmp_path)
    assert len(items) == 1
    assert items[0].kind == "photo"
    assert items[0].media_id.startswith("ph-")
