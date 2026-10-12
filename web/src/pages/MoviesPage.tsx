import { useMemo } from "react";
import { useApp } from "../context";
import { usePlayer } from "../player";
import { PosterCard } from "../components/PosterCard";
import { SetupPrompt } from "../components/SetupPrompt";
import { FilmIcon } from "../icons";

export default function MoviesPage() {
  const { items, loading, libraries, refreshAll } = useApp();
  const { play } = usePlayer();

  const hasLibrary = libraries.some((l) => l.type === "movie" || l.type === "mixed");
  const movies = useMemo(() => items.filter((i) => i.kind === "movie"), [items]);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="content-title">Movies</div>
      <div className="content-subtitle">{movies.length} movies in your library</div>

      {movies.length === 0 ? (
        hasLibrary ? (
          <div className="empty-state">
            <FilmIcon />
            <p>No movies found. Drop files into your movie folder and scan.</p>
          </div>
        ) : (
          <SetupPrompt
            icon={<FilmIcon />}
            title="Add your movies folder"
            description="Pick the folder where your movie files live. Quark will scan it for movies."
            type="movie"
            onCreated={refreshAll}
          />
        )
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
