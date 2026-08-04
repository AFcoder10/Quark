import { useMemo } from "react";
import { useApp } from "../context";
import { usePlayer } from "../player";
import { PosterCard } from "../components/PosterCard";
import { FilmIcon } from "../icons";

export default function MoviesPage() {
  const { items, loading } = useApp();
  const { play } = usePlayer();

  const movies = useMemo(() => items.filter((i) => i.kind === "movie"), [items]);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="content-title">Movies</div>
      <div className="content-subtitle">{movies.length} movies in your library</div>

      {movies.length === 0 ? (
        <div className="empty-state">
          <FilmIcon />
          <p>No movies found. Drop files into the movies library folder and scan.</p>
        </div>
      ) : (
        <div className="grid">
          {movies.map((item) => (
            <PosterCard key={item.media_id} item={item} onPlay={play} />
          ))}
        </div>
      )}
    </div>
  );
}
