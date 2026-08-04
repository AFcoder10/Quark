import { useState, type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, artworkUrl } from "../api";
import { useApp } from "../context";
import type { Item } from "../types";
import { useContextMenu } from "./ContextMenu";
import { CaptionIcon, CheckIcon, FilmStripIcon, PlayIcon, RefreshIcon, SparkIcon, TrashIcon } from "../icons";

export function PosterCard({ item, onPlay }: { item: Item; onPlay?: (item: Item) => void }) {
  const navigate = useNavigate();
  const { notify, refreshItems } = useApp();
  const menu = useContextMenu();
  const [watched, setWatched] = useState<boolean | null>(null);
  const [optimizing, setOptimizing] = useState(false);

  const poster = item.artwork?.poster || item.metadata?.artwork?.poster;
  const title = item.kind === "episode" ? item.display_title : item.display_title || item.title;
  const metaParts: string[] = [];
  if (item.year) metaParts.push(String(item.year));
  if (item.kind === "episode") {
    if (item.season != null && item.episode != null) metaParts.push(`S${item.season}E${item.episode}`);
  }

  const handleOpen = () => {
    if (item.kind === "episode" && item.series_title) {
      navigate(`/show/${encodeURIComponent(item.series_title)}`);
    } else {
      navigate(`/item/${item.media_id}`);
    }
  };

  const handlePlay = () => {
    if (onPlay) onPlay(item);
    else handleOpen();
  };

  const handleOptimize = async () => {
    if (optimizing) return;
    setOptimizing(true);
    try {
      await api.optimize(item.media_id);
      notify(`Optimization queued: ${title}`, "info");
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setOptimizing(false);
    }
  };

  const handleRefresh = async () => {
    try {
      await api.refreshItem(item.media_id);
      notify(`Refreshing metadata: ${title}`, "info");
      window.setTimeout(refreshItems, 3000);
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleSubtitles = async () => {
    try {
      await api.downloadSubtitles(item.media_id);
      notify(`Downloading subtitles: ${title}`, "info");
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${title}" from library?`)) return;
    try {
      await api.deleteItem(item.media_id);
      notify(`Removed: ${title}`, "success");
      refreshItems();
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const handleToggleWatched = async () => {
    const next = !(watched ?? false);
    setWatched(next);
    try {
      await api.markWatched(item.media_id, next);
      notify(next ? `Marked watched: ${title}` : `Marked unwatched: ${title}`, "success");
    } catch {
      setWatched(null);
    }
  };

  const onContextMenu = (e: MouseEvent<HTMLElement>) => {
    e.preventDefault();
    menu.open(e.clientX, e.clientY, [
      { label: "Play", icon: <PlayIcon />, onClick: handlePlay },
      { label: "Open details", icon: <FilmStripIcon />, onClick: handleOpen },
      { label: "---" },
      {
        label: watched ? "Mark unwatched" : "Mark watched",
        icon: <CheckIcon />,
        onClick: handleToggleWatched,
      },
      { label: "---" },
      {
        label: optimizing ? "Queued..." : "Optimize (HLS)",
        icon: <SparkIcon />,
        onClick: handleOptimize,
        danger: false,
      },
      { label: "Refresh metadata", icon: <RefreshIcon />, onClick: handleRefresh },
      { label: "Download subtitles", icon: <CaptionIcon />, onClick: handleSubtitles },
      { label: "---" },
      { label: "Remove from library", icon: <TrashIcon />, onClick: handleDelete, danger: true },
    ]);
  };

  return (
    <>
      <div
        className="poster-card"
        onClick={handleOpen}
        onContextMenu={onContextMenu}
        style={{ cursor: "context-menu" }}
      >
        {poster ? (
          <img className="poster" src={artworkUrl(item.media_id, "poster")} alt={title} loading="lazy" />
        ) : (
          <div className="poster-placeholder">
            <FilmStripIcon />
          </div>
        )}

        {item.optimized && <span className="optimized-badge">HLS</span>}
        {(watched ?? false) && <span className="watched-badge">Watched</span>}

        <div className="play-overlay-btn">
          <PlayIcon />
        </div>

        <div className="poster-overlay">
          <div>
            <div className="poster-title">{title}</div>
            {metaParts.length > 0 && <div className="poster-meta">{metaParts.join(" · ")}</div>}
          </div>
        </div>
      </div>
      {menu.render}
    </>
  );
}
