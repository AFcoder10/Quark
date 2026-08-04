import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../context";
import { RefreshIcon, SparkIcon, SearchIcon } from "../icons";

export function TopBar({ title }: { title: string }) {
  const { refreshAll, notify } = useApp();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    if (!query.trim()) return;
    const timer = window.setTimeout(() => navigate(`/search?q=${encodeURIComponent(query.trim())}`), 400);
    return () => window.clearTimeout(timer);
  }, [query, navigate]);

  const handleScanAll = async () => {
    if (scanning) return;
    setScanning(true);
    try {
      await api.scanAll();
      notify("Scan started", "info");
      window.setTimeout(async () => {
        await refreshAll();
        setScanning(false);
      }, 6000);
    } catch (error) {
      notify(String(error), "error");
      setScanning(false);
    }
  };

  return (
    <header className="topbar">
      <h1 className="topbar-title">{title}</h1>
      <div className="topbar-spacer" />
      <div className="search">
        <SearchIcon />
        <input
          placeholder="Search movies & shows..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <button className="topbar-btn" onClick={() => refreshAll()} title="Refresh">
        <RefreshIcon /> Refresh
      </button>
      <button className="topbar-btn primary" onClick={handleScanAll} title="Scan all libraries">
        <SparkIcon /> {scanning ? "Scanning..." : "Scan All"}
      </button>
    </header>
  );
}
