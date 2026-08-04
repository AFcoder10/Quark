import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, artworkUrl } from "../api";
import { useApp } from "../context";
import { usePlayer } from "../player";
import type { Item, RecentState } from "../types";
import { PosterCard } from "../components/PosterCard";
import { FilmIcon, PlayIcon, TvIcon } from "../icons";

export default function HomePage() {
  const { items, libraries, loading } = useApp();
  const { play } = usePlayer();
  const navigate = useNavigate();

  const [recents, setRecents] = useState<RecentState[]>([]);

  useEffect(() => {
    api
      .recent()
      .then(setRecents)
      .catch(() => setRecents([]));
  }, []);

  const movies = useMemo(() => items.filter((i) => i.kind === "movie"), [items]);
  const shows = useMemo(
    () =>
      items
        .filter((i) => i.kind === "episode")
        .map((i) => i.series_title)
        .filter(Boolean)
        .filter((v, idx, arr) => arr.indexOf(v) === idx),
    [items],
  );

  const continueItems = useMemo(() => {
    const list: { item: Item; state: RecentState }[] = [];
    for (const r of recents) {
      const match = items.find((i) => i.media_id === r.media_id);
      if (match) list.push({ item: match, state: r });
    }
    return list;
  }, [recents, items]);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="content-title">Home</div>
      <div className="content-subtitle">Your media library at a glance</div>

      <div className="flex gap-md mb-20" style={{ marginBottom: 26 }}>
        {libraries.map((lib) => (
          <div
            key={lib.id}
            className="lib-card"
            style={{ flex: 1, cursor: "pointer" }}
            onClick={() => navigate(lib.type === "show" ? "/shows" : "/movies")}
          >
            <div className="lib-icon">{lib.type === "show" ? <TvIcon /> : <FilmIcon />}</div>
            <div className="lib-info">
              <div className="lib-name">{lib.name}</div>
              <div className="lib-path">
                {lib.type === "show"
                  ? `${items.filter((i) => i.kind === "episode").length} episodes`
                  : `${movies.length} movies`}
              </div>
            </div>
          </div>
        ))}
      </div>

      {continueItems.length > 0 && (
        <div style={{ marginBottom: 30 }}>
          <div className="section-title">Continue Watching</div>
          <div className="continue-grid">
            {continueItems.map(({ item, state }) => {
              const poster = item.artwork?.poster || item.metadata?.artwork?.poster;
              const backdrop = item.artwork?.backdrop || item.metadata?.artwork?.backdrop;
              return (
                <div
                  key={item.media_id}
                  className="continue-card"
                  onClick={() => navigate(item.kind === "episode" && item.series_title ? `/show/${encodeURIComponent(item.series_title)}` : `/item/${item.media_id}`)}
                >
                  <div className="continue-thumb-wrap">
                    {backdrop ? (
                      <img className="continue-thumb" src={artworkUrl(item.media_id, "backdrop")} alt="" loading="lazy" />
                    ) : poster ? (
                      <img className="continue-thumb" src={artworkUrl(item.media_id, "poster")} alt="" loading="lazy" />
                    ) : (
                      <div className="continue-thumb-placeholder">
                        <FilmIcon />
                      </div>
                    )}
                    <button
                      className="continue-play-overlay"
                      onClick={(e) => {
                        e.stopPropagation();
                        play(item);
                      }}
                      title="Resume"
                    >
                      <PlayIcon />
                    </button>
                    <div className="continue-bar">
                      <div className="continue-fill" style={{ width: `${Math.min(100, Math.max(0, state.progress_pct))}%` }} />
                    </div>
                  </div>
                  <div className="continue-info">
                    <div className="continue-title">{item.series_title || item.display_title || item.title}</div>
                    {item.kind === "episode" && item.season != null && item.episode != null && (
                      <div className="continue-sub">
                        S{String(item.season).padStart(2, "0")}E{String(item.episode).padStart(2, "0")} · {item.metadata?.title || item.title}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="section-title">Movies</div>
      {movies.length === 0 ? (
        <div className="empty-state">
          <FilmIcon />
          <p>No movies found. Add files to the movies library and scan.</p>
        </div>
      ) : (
        <div className="grid">
          {movies.slice(0, 12).map((item) => (
            <PosterCard key={item.media_id} item={item} />
          ))}
        </div>
      )}

      <div className="section-title">TV Shows</div>
      {shows.length === 0 ? (
        <div className="empty-state">
          <TvIcon />
          <p>No TV shows found. Add shows using the tvshows/ShowName/S## structure.</p>
        </div>
      ) : (
        <div className="grid">
          {shows.slice(0, 12).map((seriesTitle) => {
            const ep = items.find((i) => i.series_title === seriesTitle && i.episode === 1);
            if (!ep) return null;
            return <PosterCard key={seriesTitle} item={ep} />;
          })}
        </div>
      )}
    </div>
  );
}
