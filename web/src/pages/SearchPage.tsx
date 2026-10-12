import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { usePlayer } from "../player";
import { PosterCard } from "../components/PosterCard";
import { SearchIcon } from "../icons";
import type { Item } from "../types";

type SortKey = "recently_added" | "rating" | "title" | "year";

export default function SearchPage() {
  const [params] = useSearchParams();
  const query = params.get("q") ?? "";
  const { play } = usePlayer();
  const [results, setResults] = useState<Item[]>([]);
  const [total, setTotal] = useState(0);
  const [searching, setSearching] = useState(false);
  const [genre, setGenre] = useState("");
  const [unwatched, setUnwatched] = useState(false);
  const [sort, setSort] = useState<SortKey>("recently_added");
  const [genres, setGenres] = useState<string[]>([]);

  useEffect(() => {
    api
      .genres()
      .then(setGenres)
      .catch(() => setGenres([]));
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      setTotal(0);
      return;
    }
    setSearching(true);
    const timer = window.setTimeout(async () => {
      try {
        const data = await api.queryItems({
          search: q,
          genres: genre ? [genre] : [],
          unwatched: unwatched ? true : null,
          sort,
          limit: 100,
        });
        setResults(data.items);
        setTotal(data.total);
      } catch (error) {
        console.warn("Query failed", error);
        setResults([]);
        setTotal(0);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query, genre, unwatched, sort]);

  const hasQuery = query.trim().length > 0;

  return (
    <div>
      <div className="content-title">Search</div>
      <div className="content-subtitle">
        {hasQuery
          ? `${total} result${total === 1 ? "" : "s"} for "${query.trim()}"`
          : "Type in the search bar above"}
      </div>

      {hasQuery && (
        <div className="filter-row">
          <select value={genre} onChange={(e) => setGenre(e.target.value)}>
            <option value="">All genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
          <label className="filter-check">
            <input type="checkbox" checked={unwatched} onChange={(e) => setUnwatched(e.target.checked)} />
            Unwatched only
          </label>
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="recently_added">Recently added</option>
            <option value="rating">Rating</option>
            <option value="title">Title A–Z</option>
            <option value="year">Year</option>
          </select>
        </div>
      )}

      {searching ? (
        <div className="spinner" />
      ) : results.length === 0 && hasQuery ? (
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
