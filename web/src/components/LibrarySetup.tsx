import { useEffect, useState } from "react";
import { api } from "../api";
import { useApp } from "../context";
import { FolderIcon } from "../icons";

export const LIBRARY_LABELS: Record<string, string> = {
  movie: "Movies",
  show: "TV Shows",
  music: "Music",
  photo: "Photos",
  mixed: "Movies & TV",
};

interface Props {
  /** Library type this setup creates. */
  type: "movie" | "show" | "music" | "photo" | "mixed";
  /** Called after the folder is saved (so the caller can refresh/scan). */
  onCreated?: () => void;
  /** Render as a modal (from Settings) instead of an inline card. */
  asModal?: boolean;
  onClose?: () => void;
}

/**
 * Zero-hardcoding folder setup. Lets the user browse the device filesystem and
 * pick the folder for this library type, then saves it to the local DB.
 */
export function LibrarySetup({ type, onCreated, asModal, onClose }: Props) {
  const { refreshLibraries, notify } = useApp();
  const [name, setName] = useState(LIBRARY_LABELS[type] ?? "Library");
  const [path, setPath] = useState("");
  const [browsing, setBrowsing] = useState(false);
  const [current, setCurrent] = useState<string | null>(null);
  const [parent, setParent] = useState<string | null>(null);
  const [homeDir, setHomeDir] = useState<string>("");
  const [entries, setEntries] = useState<{ name: string; path: string }[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openBrowser = async (target?: string) => {
    setBrowsing(true);
    setError(null);
    try {
      const res = await api.browse(target);
      setCurrent(res.path);
      setParent(res.parent);
      setHomeDir(res.home);
      setEntries(res.entries);
      setPath(res.path);
    } catch (err) {
      setError(String(err));
    }
  };

  useEffect(() => {
    // default the name when the type changes
    setName(LIBRARY_LABELS[type] ?? "Library");
  }, [type]);

  const save = async () => {
    if (!path.trim()) {
      setError("Pick a folder first.");
      return;
    }
    setSaving(true);
    try {
      await api.addLibrary({ name: name.trim() || LIBRARY_LABELS[type], path: path.trim(), type });
      await refreshLibraries();
      notify(`${LIBRARY_LABELS[type]} folder added`, "success");
      onCreated?.();
      onClose?.();
    } catch (err) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  };

  const body = (
    <>
      <div className="form-field">
        <label>Library name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder={LIBRARY_LABELS[type]} />
      </div>

      <div className="form-field">
        <label>Folder</label>
        <div className="folder-pick">
          <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="Choose a folder…" />
          <button className="btn btn-ghost" type="button" onClick={() => openBrowser(current ?? undefined)}>
            <FolderIcon /> Browse
          </button>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      {browsing && (
        <div className="browser">
          <div className="browser-bar">
            <button className="btn btn-ghost btn-sm" type="button" onClick={() => openBrowser(homeDir)}>
              Home
            </button>
            {parent && (
              <button className="btn btn-ghost btn-sm" type="button" onClick={() => openBrowser(parent)}>
                ↑ Up
              </button>
            )}
            <span className="browser-path" title={current ?? ""}>
              {current}
            </span>
          </div>
          <div className="browser-list">
            {entries.length === 0 && <div className="browser-empty">No subfolders</div>}
            {entries.map((entry) => (
              <button
                key={entry.path}
                className="browser-item"
                type="button"
                onClick={() => openBrowser(entry.path)}
              >
                <FolderIcon /> {entry.name}
              </button>
            ))}
          </div>
          <div className="browser-actions">
            <button className="btn btn-primary btn-sm" type="button" onClick={() => setBrowsing(false)}>
              Use this folder
            </button>
          </div>
        </div>
      )}

      <div className="modal-actions">
        {onClose && (
          <button className="btn btn-ghost" type="button" onClick={onClose}>
            Cancel
          </button>
        )}
        <button className="btn btn-primary" type="button" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Add folder"}
        </button>
      </div>
    </>
  );

  if (asModal) {
    return (
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <h3>Set up {LIBRARY_LABELS[type]}</h3>
          {body}
        </div>
      </div>
    );
  }

  return <div className="setup-card">{body}</div>;
}
