import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Show } from "../types";
import { TvIcon, StarIcon } from "../icons";

export default function ShowsPage() {
  const navigate = useNavigate();
  const [shows, setShows] = useState<Show[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .shows()
      .then(setShows)
      .catch(() => setShows([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="content-title">TV Shows</div>
      <div className="content-subtitle">{shows.length} shows in your library</div>

      {shows.length === 0 ? (
        <div className="empty-state">
          <TvIcon />
          <p>
            No shows found. Use the structure <b>tvshows/ShowName/S01/ep1.mp4</b> and scan.
          </p>
        </div>
      ) : (
        <div className="show-grid">
          {shows.map((show) => {
            const poster = show.artwork_urls?.poster;
            const backdrop = show.artwork_urls?.backdrop;
            return (
              <div
                key={show.series_title}
                className="show-card"
                onClick={() => navigate(`/show/${encodeURIComponent(show.series_title)}`)}
                onContextMenu={(e) => e.preventDefault()}
              >
                {backdrop && (
                  <img className="show-card-backdrop" src={backdrop} alt="" loading="lazy" />
                )}
                <div className="show-card-scrim" />
                {poster ? (
                  <img className="show-card-poster" src={poster} alt={show.series_title} loading="lazy" />
                ) : (
                  <div className="show-card-poster poster-placeholder">
                    <TvIcon />
                  </div>
                )}
                <div className="show-card-info">
                  <div className="show-card-title">{show.series_title}</div>
                  <div className="show-card-meta">
                    {show.rating != null && (
                      <span className="show-card-rating">
                        <StarIcon /> {show.rating.toFixed(1)}
                      </span>
                    )}
                    <span>{show.episode_count ?? 0} eps</span>
                    {show.networks?.[0] && <span>{show.networks[0]}</span>}
                    {show.year != null && <span>{show.year}</span>}
                  </div>
                  {show.status && <span className={`status-dot ${show.status.toLowerCase() === "ended" ? "ended" : "airing"}`} />}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
