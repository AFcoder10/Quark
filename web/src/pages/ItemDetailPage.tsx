import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, artworkUrl } from "../api";
import { useApp } from "../context";
import { usePlayer } from "../player";
import { CaptionIcon, CheckIcon, PlayIcon, RefreshIcon, SparkIcon, TrashIcon } from "../icons";

export default function ItemDetailPage() {
  const { mediaId } = useParams();
  const { items, notify, refreshItems } = useApp();
  const { play } = usePlayer();
  const [item, setItem] = useState<Awaited<ReturnType<typeof api.item>> | null>(null);
  const [watched, setWatched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);

  const load = useCallback(async () => {
    if (!mediaId) return;
    setLoading(true);
    try {
      const data = await api.item(mediaId);
      setItem(data);
      const state = await api.state(mediaId);
      setWatched(state.watched);
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setLoading(false);
    }
  }, [mediaId, notify]);

  useEffect(() => {
    load();
  }, [load]);

  const meta = item?.metadata;

  const handleOptimize = async (mode: "hls" | "hevc" = "hls") => {
    if (!item || optimizing) return;
    setOptimizing(true);
    try {
      await api.optimize(item.media_id, mode);
      notify(`Queued for ${mode.toUpperCase()} optimization`, "info");
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setOptimizing(false);
    }
  };

  const handleRefresh = async () => {
    if (!item) return;
    try {
      await api.refreshItem(item.media_id);
      notify("Metadata refresh started", "info");
      window.setTimeout(load, 3500);
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleSubtitles = async () => {
    if (!item) return;
    try {
      await api.downloadSubtitles(item.media_id);
      notify("Subtitle download started", "info");
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleDelete = async () => {
    if (!item) return;
    if (!window.confirm(`Remove "${item.display_title}" from the library?`)) return;
    try {
      await api.deleteItem(item.media_id);
      notify("Item removed", "success");
      refreshItems();
      window.history.back();
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleToggleWatched = async () => {
    if (!item) return;
    const next = !watched;
    setWatched(next);
    try {
      await api.markWatched(item.media_id, next);
      notify(next ? "Marked watched" : "Marked unwatched", "success");
    } catch {
      setWatched(!next);
    }
  };

  const subtitleTracks = useMemo(() => meta?.subtitles ?? [], [meta]);

  if (loading) return <div className="spinner" />;
  if (!item || !meta) {
    return (
      <div className="empty-state">
        <p>Item not found or metadata missing. Trigger a metadata refresh from the library view.</p>
        <Link to="/" className="btn btn-ghost mt-20">Back home</Link>
      </div>
    );
  }

  const poster = meta.artwork?.poster;
  const backdrop = meta.artwork?.backdrop;
  const isMovie = item.kind === "movie";

  return (
    <div className="detail" onContextMenu={(e) => e.preventDefault()}>
      <div className="hero">
        {backdrop && <img className="hero-backdrop hero-backdrop-wide" src={artworkUrl(item.media_id, "backdrop")} alt="" />}
        <div className="hero-gradient" />
        <div className="hero-content">
          {poster ? (
            <img className="hero-poster" src={artworkUrl(item.media_id, "poster")} alt={meta.title} />
          ) : (
            <div className="hero-poster poster-placeholder" />
          )}
          <div className="hero-info">
            {isMovie && meta.artwork?.logo && (
              <img className="hero-logo" src={artworkUrl(item.media_id, "logo")} alt={meta.title} />
            )}
            <div className="hero-title">{meta.series_title || meta.title}</div>
            <div className="hero-tags">
              {item.kind === "episode" && meta.season != null && meta.episode != null && (
                <span className="chip">S{String(meta.season).padStart(2, "0")}E{String(meta.episode).padStart(2, "0")}</span>
              )}
              {isMovie && <span className="chip">Movie</span>}
              {meta.year && <span className="chip">{meta.year}</span>}
              {meta.certification && <span className="chip">{meta.certification}</span>}
              {meta.runtime && <span className="chip">{Math.round(meta.runtime / 60)} min</span>}
              {meta.rating && <span className="chip rating-chip">★ {meta.rating.toFixed(1)}</span>}
              {meta.status && !isMovie && <span className="chip">{meta.status}</span>}
              {meta.genres?.map((g) => <span key={g} className="chip">{g}</span>)}
            </div>
            {meta.tagline && <div className="hero-tagline">"{meta.tagline}"</div>}
            {meta.overview && <div className="hero-overview">{meta.overview}</div>}
            {(meta.creators?.length ?? 0) > 0 && (
              <div className="hero-credit">
                <strong>Created by</strong> {meta.creators!.join(", ")}
              </div>
            )}
            {(meta.production_companies?.length ?? 0) > 0 && (
              <div className="hero-credit">
                <strong>Studio</strong> {meta.production_companies!.slice(0, 3).join(", ")}
              </div>
            )}
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={() => play(item)}>
                <PlayIcon /> Play
              </button>
              <button className="btn btn-ghost" onClick={handleToggleWatched}>
                <CheckIcon /> {watched ? "Watched" : "Mark watched"}
              </button>
              <button className="btn btn-ghost" onClick={() => handleOptimize("hls")}>
                <SparkIcon /> {optimizing ? "Queued..." : "Optimize (HLS)"}
              </button>
              <button className="btn btn-ghost" onClick={() => handleOptimize("hevc")}>
                ⚡ {optimizing ? "Queued..." : "Compress (HEVC H.265)"}
              </button>
              <button className="btn btn-ghost" onClick={handleRefresh}>
                <RefreshIcon /> Refresh
              </button>
              <button className="btn btn-ghost" onClick={handleSubtitles}>
                <CaptionIcon /> Subtitles
              </button>
              <button className="btn btn-danger" onClick={handleDelete}>
                <TrashIcon /> Remove
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="detail-body">
        <div className="flex gap-md">
          <Link to={item.kind === "episode" ? "/shows" : "/movies"} className="btn btn-ghost" style={{ textDecoration: "none" }}>
            ← Back
          </Link>
          {item.optimized && <span className="optimized-badge" style={{ position: "static" }}>HLS optimized</span>}
        </div>

        <div className="section-title">Technical Details</div>
        <div className="meta-grid">
          <div className="meta-card">
            <div className="label">Video Codec</div>
            <div className="value">{meta.video?.codec ?? "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">Resolution</div>
            <div className="value">{meta.video?.width && meta.video?.height ? `${meta.video.width}×${meta.video.height}` : "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">Frame Rate</div>
            <div className="value">{meta.video?.fps ? `${meta.video.fps} fps` : "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">Bitrate</div>
            <div className="value">{meta.video?.bitrate ? `${Math.round(meta.video.bitrate / 1000)} kbps` : "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">Playback Mode</div>
            <div className="value">{meta.playback?.mode ?? "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">TMDB</div>
            <div className="value">{meta.tmdb_id ?? "—"}</div>
          </div>
          <div className="meta-card">
            <div className="label">IMDB</div>
            <div className="value">{meta.imdb_id ?? "—"}</div>
          </div>
          {meta.vote_count != null && (
            <div className="meta-card">
              <div className="label">Vote Count</div>
              <div className="value">{meta.vote_count.toLocaleString()}</div>
            </div>
          )}
          {meta.popularity != null && (
            <div className="meta-card">
              <div className="label">Popularity</div>
              <div className="value">{meta.popularity.toFixed(1)}</div>
            </div>
          )}
          {meta.first_air_date && (
            <div className="meta-card">
              <div className="label">First Aired</div>
              <div className="value">{meta.first_air_date}</div>
            </div>
          )}
          {meta.last_air_date && (
            <div className="meta-card">
              <div className="label">Last Aired</div>
              <div className="value">{meta.last_air_date}</div>
            </div>
          )}
          {meta.networks && meta.networks.length > 0 && (
            <div className="meta-card">
              <div className="label">Network</div>
              <div className="value">{meta.networks.join(", ")}</div>
            </div>
          )}
          {meta.spoken_languages && meta.spoken_languages.length > 0 && (
            <div className="meta-card">
              <div className="label">Languages</div>
              <div className="value">{meta.spoken_languages.join(", ")}</div>
            </div>
          )}
          {isMovie && meta.production_companies && meta.production_companies.length > 0 && (
            <div className="meta-card">
              <div className="label">Companies</div>
              <div className="value">{meta.production_companies.join(", ")}</div>
            </div>
          )}
        </div>

        {meta.audio && meta.audio.length > 0 && (
          <>
            <div className="section-title">Audio Tracks</div>
            <div className="meta-grid">
              {meta.audio.map((track, idx) => (
                <div key={idx} className="meta-card">
                  <div className="label">Track {idx + 1}{track.language ? ` · ${track.language}` : ""}</div>
                  <div className="value">{track.codec ?? "—"}{track.channels ? ` · ${track.channels}ch` : ""}</div>
                </div>
              ))}
            </div>
          </>
        )}

        {subtitleTracks.length > 0 && (
          <>
            <div className="section-title">Subtitles</div>
            <div className="meta-grid">
              {subtitleTracks.map((track, idx) => (
                <div key={idx} className="meta-card">
                  <div className="label">Track {idx + 1}</div>
                  <div className="value">
                    {track.language ?? track.title ?? track.format ?? "Unknown"}
                    {track.forced ? " · forced" : ""}
                    {track.embedded ? "" : " · downloaded"}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
