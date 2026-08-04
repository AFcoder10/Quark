import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { useApp } from "../context";
import { usePlayer } from "../player";
import { PosterCard } from "../components/PosterCard";
import { SearchIcon } from "../icons";

export default function SearchPage() {
  const [params] = useSearchParams();
  const query = params.get("q") ?? "";
  const { items, loading } = useApp();
  const { play } = usePlayer();

  const results = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return [];
    return items.filter((item) => {
      const haystack = `${item.display_title} ${item.title} ${item.series_title ?? ""} ${item.year ?? ""}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [items, query]);

  return (
    <div>
      <div className="content-title">Search</div>
      <div className="content-subtitle">
        {query ? `${results.length} results for "${query}"` : "Type in the search bar above"}
      </div>

      {loading ? (
        <div className="spinner" />
      ) : results.length === 0 && query ? (
        <div className="empty-state">
          <SearchIcon />
          <p>No matches found</p>
        </div>
      ) : (
        <div className="grid">
          {results.map((item) => (
            <PosterCard key={item.media_id} item={item} onPlay={play} />
          ))}
        </div>
      )}
    </div>
  );
}
