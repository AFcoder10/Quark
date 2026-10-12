import { useEffect, useMemo, useRef, useState } from "react";
import { api, streamUrl } from "../api";
import { useApp } from "../context";
import type { Album, Artist, Track } from "../types";
import { MusicIcon, PlayIcon } from "../icons";
import { SetupPrompt } from "../components/SetupPrompt";
import "../components/Music.css";

export default function MusicPage() {
  const { libraries, refreshAll } = useApp();
  const [artists, setArtists] = useState<Artist[]>([]);
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selectedArtist, setSelectedArtist] = useState<string | null>(null);
  const [openAlbum, setOpenAlbum] = useState<Album | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [nowPlaying, setNowPlaying] = useState<Track | null>(null);

  useEffect(() => {
    Promise.all([api.artists(), api.albums()])
      .then(([a, al]) => {
        setArtists(a);
        setAlbums(al);
      })
      .finally(() => setLoading(false));
  }, []);

  const reload = () =>
    Promise.all([api.artists(), api.albums()]).then(([a, al]) => {
      setArtists(a);
      setAlbums(al);
    });

  const visibleAlbums = useMemo(
    () => (selectedArtist ? albums.filter((a) => a.artist === selectedArtist) : albums),
    [albums, selectedArtist],
  );

  const openAlbumDetail = async (album: Album) => {
    const detail = await api.album(album.artist, album.album);
    setTracks(detail.tracks);
    setOpenAlbum(album);
  };

  const playTrack = (track: Track) => {
    setNowPlaying(track);
    const el = audioRef.current;
    if (!el) return;
    el.src = streamUrl(track.media_id, "direct");
    el.play().catch(() => undefined);
  };

  if (loading) return <div className="spinner" />;

  const hasLibrary = libraries.some((l) => l.type === "music");

  return (
    <div>
      {artists.length === 0 ? (
        hasLibrary ? (
          <div className="empty-state">
            <MusicIcon />
            <p>No music found. Drop audio files into your music folder and scan.</p>
          </div>
        ) : (
          <SetupPrompt
            icon={<MusicIcon />}
            title="Add your music folder"
            description="Pick the folder where your music lives. Quark reads tags (artist, album, track) automatically."
            type="music"
            onCreated={() => {
              refreshAll();
              reload();
            }}
          />
        )
      ) : (
        <>
          <div className="content-title">Music</div>
          <div className="content-subtitle">
            {artists.length} artists · {albums.length} albums
          </div>

          <div className="chip-row">
            <button
              className={`chip${selectedArtist === null ? " active" : ""}`}
              onClick={() => setSelectedArtist(null)}
            >
              All
            </button>
            {artists.map((a) => (
              <button
                key={a.artist}
                className={`chip${selectedArtist === a.artist ? " active" : ""}`}
                onClick={() => setSelectedArtist(a.artist === selectedArtist ? null : a.artist)}
              >
                {a.artist}
              </button>
            ))}
          </div>

          <div className="album-grid">
            {visibleAlbums.map((album) => (
              <div key={`${album.artist}-${album.album}`} className="album-card" onClick={() => openAlbumDetail(album)}>
                <div className="album-cover">
                  {album.cover_media_id ? (
                    <img src={`/api/items/${album.cover_media_id}/thumbnail`} alt={album.album} loading="lazy" />
                  ) : (
                    <MusicIcon />
                  )}
                </div>
                <div className="album-title">{album.album}</div>
                <div className="album-artist">{album.artist}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {openAlbum && (
        <div className="album-drawer">
          <div className="album-drawer-head">
            <div>
              <div className="content-title">{openAlbum.album}</div>
              <div className="content-subtitle">{openAlbum.artist}</div>
            </div>
            <button className="btn btn-ghost" onClick={() => setOpenAlbum(null)}>
              Close
            </button>
          </div>
          <div className="track-list">
            {tracks.map((track) => (
              <button
                key={track.media_id}
                className={`track-row${nowPlaying?.media_id === track.media_id ? " active" : ""}`}
                onClick={() => playTrack(track)}
              >
                <span className="track-num">{track.track_number ?? "•"}</span>
                <span className="track-title">{track.title}</span>
                <span className="track-dur">{formatDuration(track.duration)}</span>
                <PlayIcon />
              </button>
            ))}
          </div>
        </div>
      )}

      {nowPlaying && (
        <div className="now-playing">
          <div className="np-info">
            <div className="np-title">{nowPlaying.title}</div>
            <div className="np-artist">{nowPlaying.artist}</div>
          </div>
          <audio ref={audioRef} controls autoPlay className="np-audio" />
        </div>
      )}
      {!nowPlaying && <audio ref={audioRef} />}
    </div>
  );
}

function formatDuration(seconds?: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
