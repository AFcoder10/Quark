import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useApp } from "../context";
import { usePlayer } from "../player";
import type { Item, Show, ShowEpisode } from "../types";
import { PlayIcon, StarIcon, QueueIcon } from "../icons";
import { api } from "../api";

function formatDate(date?: string | null): string {
  if (!date) return "";
  const [y, m, d] = date.split("-");
  if (!y || !m || !d) return date;
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[Number(m) - 1]} ${Number(d)}, ${y}`;
}

export default function ShowDetailPage() {
  const { title } = useParams();
  const { notify, refreshItems } = useApp();
  const { play } = usePlayer();
  const [show, setShow] = useState<Show | null>(null);
  const [loading, setLoading] = useState(true);
  const [seasonNum, setSeasonNum] = useState<number>(1);
  const [optimizing, setOptimizing] = useState<string | null>(null);

  const decoded = useMemo(() => (title ? decodeURIComponent(title) : ""), [title]);

  useEffect(() => {
    setLoading(true);
    setShow(null);
    setSeasonNum(1);
    api
      .show(decoded)
      .then((data) => {
        setShow(data);
        if (data.seasons.length > 0) setSeasonNum(data.seasons[0].season_number);
      })
      .catch(() => setShow(null))
      .finally(() => setLoading(false));
  }, [decoded]);

  const activeSeason = useMemo(
    () => show?.seasons.find((s) => s.season_number === seasonNum) ?? null,
    [show, seasonNum],
  );

  const handleOptimize = async (ep: ShowEpisode) => {
    if (!ep.media_id) return;
    setOptimizing(ep.media_id);
    try {
      await api.optimize(ep.media_id);
      notify(`Optimization queued: ${ep.title ?? ep.local_title ?? ""}`, "info");
      refreshItems();
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setOptimizing(null);
    }
  };

  const playEpisode = (ep: ShowEpisode) => {
    if (!ep.media_id) return;
    const item: Item = {
      media_id: ep.media_id,
      kind: "episode",
      library_id: "",
      title: ep.local_title ?? ep.title ?? "",
      display_title: `S${activeSeason?.season_number ?? ""}E${ep.episode_number ?? ""} · ${ep.title ?? ""}`,
      primary_file: "",
      has_metadata: true,
      optimized: ep.optimized,
      artwork: {},
      series_title: decoded,
      season: activeSeason?.season_number,
      episode: ep.episode_number,
    };
    play(item);
  };

  if (loading) {
    return (
      <div className="detail">
        <div className="hero skeleton-hero" />
        <div className="detail-body">
          <div className="skeleton-block" style={{ height: 40, width: 200 }} />
          <div className="skeleton-block" style={{ height: 16, width: "100%", marginTop: 16 }} />
          <div className="skeleton-block" style={{ height: 16, width: "70%", marginTop: 8 }} />
        </div>
      </div>
    );
  }

  if (!show) {
    return (
      <div className="detail detail-empty">
        <h2>Show not found</h2>
        <Link to="/shows" className="btn btn-ghost" style={{ textDecoration: "none" }}>
          ← Back to shows
        </Link>
      </div>
    );
  }

  const heroArt = show.artwork_urls?.backdrop;
  const logoArt = show.artwork_urls?.logo;
  const posterArt = show.artwork_urls?.poster;
  const firstEp = show.seasons[0]?.episodes.find((e) => e.has_file);
  const localCount = show.episode_count ?? show.seasons.reduce((n, s) => n + s.episodes.filter((e) => e.has_file).length, 0);

  return (
    <div className="detail">
      <div className="hero show-hero">
        {heroArt && <img className="hero-backdrop hero-backdrop-wide" src={heroArt} alt="" />}
        <div className="hero-gradient" />
        <div className="hero-content show-hero-content">
          {posterArt && <img className="hero-poster" src={posterArt} alt={show.series_title} />}
          <div className="hero-info">
            {logoArt && <img className="hero-logo" src={logoArt} alt={show.series_title} />}
            <div className="hero-title">{show.series_title}</div>
            <div className="hero-tags">
              {show.rating != null && (
                <span className="chip rating-chip">
                  <StarIcon /> {show.rating.toFixed(1)}
                </span>
              )}
              <span className="chip">{show.number_of_seasons ?? show.seasons.length} seasons</span>
              <span className="chip">{localCount} local</span>
              <span className="chip">{show.status ?? "Ongoing"}</span>
              {show.year != null && <span className="chip">{show.year}</span>}
              {show.networks?.slice(0, 2).map((n) => (
                <span key={n} className="chip">{n}</span>
              ))}
              {show.genres?.slice(0, 3).map((g) => (
                <span key={g} className="chip">{g}</span>
              ))}
            </div>
            {show.overview && <div className="hero-overview">{show.overview}</div>}
            {show.creators && show.creators.length > 0 && (
              <div className="hero-credit">
                <strong>Created by</strong> {show.creators.join(", ")}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="detail-body">
        <div className="show-actions">
          <Link to="/shows" className="btn btn-ghost" style={{ textDecoration: "none" }}>
            ← Shows
          </Link>
          {firstEp && (
            <button className="btn btn-primary" onClick={() => playEpisode(firstEp)}>
              <PlayIcon /> Play
            </button>
          )}
        </div>

        {show.seasons.length > 1 && (
          <div className="season-tabs">
            {show.seasons.map((s) => (
              <button
                key={s.season_number}
                className={`season-tab ${seasonNum === s.season_number ? "active" : ""}`}
                onClick={() => setSeasonNum(s.season_number)}
              >
                {s.name}
                <span className="season-count">
                  {s.episodes.filter((e) => e.has_file).length}/{s.episodes.length}
                </span>
              </button>
            ))}
          </div>
        )}

        {activeSeason && (
          <div className="episode-list">
            {activeSeason.episodes.map((ep) => (
              <div
                key={ep.episode_number ?? ep.title}
                className={`episode-row episode-rich ${ep.has_file ? "" : "unavailable"}`}
                onClick={() => ep.has_file && playEpisode(ep)}
              >
                <div className="episode-num">
                  {String(ep.episode_number ?? "").padStart(2, "0")}
                </div>
                {ep.still ? (
                  <img className="episode-thumb" src={ep.still} alt="" loading="lazy" />
                ) : (
                  <div className="episode-thumb-placeholder">
                    S{activeSeason.season_number}E{String(ep.episode_number ?? "").padStart(2, "0")}
                  </div>
                )}
                <div className="episode-info">
                  <div className="episode-head">
                    <span className="episode-name">{ep.title ?? ep.local_title ?? `Episode ${ep.episode_number}`}</span>
                    <span className="episode-meta">
                      {ep.rating != null && (
                        <span className="ep-rating">
                          <StarIcon /> {ep.rating.toFixed(1)}
                        </span>
                      )}
                      {formatDate(ep.air_date) && <span>{formatDate(ep.air_date)}</span>}
                      {ep.runtime != null && <span>{ep.runtime} min</span>}
                      {ep.optimized && <span className="chip chip-hls">HLS</span>}
                      {ep.has_file && ep.media_id === optimizing && <span className="chip">queued…</span>}
                    </span>
                  </div>
                  {ep.overview && <div className="episode-overview">{ep.overview}</div>}
                  {!ep.has_file && (
                    <div className="episode-missing">Episode not available on this server</div>
                  )}
                </div>
                {ep.has_file && (
                  <div className="episode-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="icon-btn"
                      title="Optimize to HLS"
                      disabled={ep.media_id === optimizing || ep.optimized}
                      onClick={() => handleOptimize(ep)}
                    >
                      <QueueIcon />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
