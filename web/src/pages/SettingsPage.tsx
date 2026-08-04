import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useApp } from "../context";
import type { Library, Settings } from "../types";
import { FilmIcon, FolderIcon, PlusIcon, RefreshIcon, RestartIcon, SparkIcon, TrashIcon, TvIcon } from "../icons";

type Section = "server" | "libraries" | "streaming" | "optimization" | "providers";

export default function SettingsPage() {
  const { notify, refreshLibraries, libraries, refreshAll } = useApp();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [section, setSection] = useState<Section>("server");
  const [saving, setSaving] = useState(false);
  const [showAddLib, setShowAddLib] = useState(false);
  const [newLib, setNewLib] = useState({ name: "", path: "", type: "movie" });
  const [scanning, setScanning] = useState<string | null>(null);
  const [showRestartConfirm, setShowRestartConfirm] = useState(false);
  const [restarting, setRestarting] = useState(false);

  const loadSettings = async () => {
    try {
      setSettings(await api.settings());
    } catch (error) {
      notify(String(error), "error");
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await api.saveSettings(settings);
      notify("Settings saved", "success");
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setSaving(false);
    }
  };

  const restartServer = async () => {
    setRestarting(true);
    try {
      await api.restartServer();
      notify("Server is restarting...", "info");
      setShowRestartConfirm(false);
      // The server disconnects during restart; refresh when it comes back up.
      let attempts = 0;
      const checkHealth = async () => {
        attempts += 1;
        if (attempts > 30) return;
        try {
          await api.health();
          await refreshAll();
          notify("Server restarted", "success");
        } catch {
          window.setTimeout(checkHealth, 1000);
        }
      };
      window.setTimeout(checkHealth, 3000);
    } catch (error) {
      notify(String(error), "error");
    } finally {
      setRestarting(false);
    }
  };

  const addLibrary = async () => {
    if (!newLib.name.trim() || !newLib.path.trim()) {
      notify("Name and path are required", "error");
      return;
    }
    try {
      await api.addLibrary({ name: newLib.name.trim(), path: newLib.path.trim(), type: newLib.type });
      notify("Library added", "success");
      setShowAddLib(false);
      setNewLib({ name: "", path: "", type: "movie" });
      refreshLibraries();
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const removeLibrary = async (lib: Library) => {
    if (!window.confirm(`Remove library "${lib.name}"?`)) return;
    try {
      await api.removeLibrary(lib.id);
      notify("Library removed", "success");
      refreshLibraries();
    } catch (error) {
      notify(String(error), "error");
    }
  };

  const scanLibrary = async (lib: Library) => {
    if (scanning) return;
    setScanning(lib.id);
    try {
      await api.scanLibrary(lib.id);
      notify(`Scan started: ${lib.name}`, "info");
      window.setTimeout(refreshAll, 6000);
    } catch (error) {
      notify(String(error), "error");
    } finally {
      window.setTimeout(() => setScanning(null), 2000);
    }
  };

  const scanAll = async () => {
    if (scanning) return;
    setScanning("all");
    try {
      await api.scanAll();
      notify("Scan all libraries started", "info");
      window.setTimeout(refreshAll, 8000);
    } catch (error) {
      notify(String(error), "error");
    } finally {
      window.setTimeout(() => setScanning(null), 3000);
    }
  };

  const setField = (section: Section, field: string, value: unknown) => {
    if (!settings || section === "libraries") return;
    setSettings({
      ...settings,
      [section]: { ...(settings[section as keyof Settings] as object), [field]: value },
    });
  };

  const keyValue = (value: string): { display: string; isMasked: boolean } =>
    value === "***" ? { display: "", isMasked: true } : { display: value, isMasked: false };

  const sections: { id: Section; label: string }[] = [
    { id: "server", label: "Server" },
    { id: "libraries", label: "Libraries" },
    { id: "streaming", label: "Streaming" },
    { id: "optimization", label: "Optimization" },
    { id: "providers", label: "Providers" },
  ];

  const titleFor = useMemo(() => {
    switch (section) {
      case "server": return "Server Configuration";
      case "libraries": return "Media Libraries";
      case "streaming": return "Streaming";
      case "optimization": return "Optimization";
      case "providers": return "Metadata Providers";
    }
  }, [section]);

  if (!settings) return <div className="spinner" />;

  return (
    <div>
      <div className="content-title">Settings</div>
      <div className="content-subtitle">Configure Quark to your liking</div>

      <div className="settings-grid mt-20">
        <div className="settings-nav">
          {sections.map((s) => (
            <button key={s.id} className={section === s.id ? "active" : ""} onClick={() => setSection(s.id)}>
              {s.label}
            </button>
          ))}
        </div>

        <div className="settings-panel">
          <h3>{titleFor}</h3>

          {section === "server" && (
            <>
              <div className="settings-field">
                <label>Host</label>
                <input
                  value={settings.server.host}
                  onChange={(e) => setField("server", "host", e.target.value)}
                />
              </div>
              <div className="settings-field">
                <label>Port</label>
                <input
                  type="number"
                  value={settings.server.port}
                  onChange={(e) => setField("server", "port", Number(e.target.value))}
                />
              </div>
              <div className="settings-field">
                <label>Log Level</label>
                <select
                  value={settings.server.log_level}
                  onChange={(e) => setField("server", "log_level", e.target.value)}
                >
                  {["DEBUG", "INFO", "WARNING", "ERROR"].map((lvl) => (
                    <option key={lvl} value={lvl}>{lvl}</option>
                  ))}
                </select>
              </div>
              <div className="checkbox-field">
                <input
                  type="checkbox"
                  id="scan_on_startup"
                  checked={settings.server.scan_on_startup}
                  onChange={(e) => setField("server", "scan_on_startup", e.target.checked)}
                />
                <label htmlFor="scan_on_startup">Scan libraries on server start</label>
              </div>
              <p className="panel-desc">
                Changing host/port requires a server restart.
              </p>
              <div className="flex gap-md mt-20">
                <button className="btn btn-primary" onClick={() => setShowRestartConfirm(true)}>
                  <RestartIcon /> Restart Server
                </button>
              </div>
            </>
          )}

          {section === "libraries" && (
            <>
              <div className="flex gap-md mb-20">
                <button className="btn btn-primary" onClick={() => setShowAddLib(true)}>
                  <PlusIcon /> Add Library
                </button>
                <button className="btn btn-ghost" onClick={scanAll}>
                  <RefreshIcon /> {scanning === "all" ? "Scanning..." : "Scan All"}
                </button>
              </div>
              {libraries.length === 0 && <p className="panel-desc">No libraries configured.</p>}
              {libraries.map((lib) => (
                <div key={lib.id} className="lib-card">
                  <div className="lib-icon">{lib.type === "show" ? <TvIcon /> : <FilmIcon />}</div>
                  <div className="lib-info">
                    <div className="lib-name">{lib.name}</div>
                    <div className="lib-path">{lib.path_resolved}</div>
                  </div>
                  <span className="lib-type">{lib.type}</span>
                  <div className="lib-actions">
                    <button className="icon-btn" title="Scan" onClick={() => scanLibrary(lib)}>
                      <RefreshIcon />
                    </button>
                    <button className="icon-btn danger" title="Remove" onClick={() => removeLibrary(lib)}>
                      <TrashIcon />
                    </button>
                  </div>
                </div>
              ))}
              <p className="panel-desc">
                Movies go in <b>media/movies/</b>. TV shows use <b>media/tvshows/ShowName/S01/ep1.mp4</b>.
              </p>
            </>
          )}

          {section === "streaming" && (
            <>
              <div className="settings-field">
                <label>Default Playback Mode</label>
                <select
                  value={settings.streaming.default_mode}
                  onChange={(e) => setField("streaming", "default_mode", e.target.value)}
                >
                  {["auto", "direct", "hls", "transcode"].map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <div className="hint">auto = direct play when supported, otherwise HLS or live transcode</div>
              </div>
              <div className="settings-field">
                <label>Live Transcode Height</label>
                <input
                  type="number"
                  value={settings.streaming.live_transcode_height}
                  onChange={(e) => setField("streaming", "live_transcode_height", Number(e.target.value))}
                />
              </div>
              <div className="settings-field">
                <label>Live Idle Timeout (seconds)</label>
                <input
                  type="number"
                  value={settings.streaming.live_idle_seconds}
                  onChange={(e) => setField("streaming", "live_idle_seconds", Number(e.target.value))}
                />
              </div>
              <div className="settings-field">
                <label>Direct Play Codecs</label>
                <input
                  value={settings.streaming.direct_play_codecs.join(", ")}
                  onChange={(e) =>
                    setField(
                      "streaming",
                      "direct_play_codecs",
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    )
                  }
                />
              </div>
              <div className="settings-field">
                <label>Direct Play Containers</label>
                <input
                  value={settings.streaming.direct_play_containers.join(", ")}
                  onChange={(e) =>
                    setField(
                      "streaming",
                      "direct_play_containers",
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    )
                  }
                />
              </div>
            </>
          )}

          {section === "optimization" && (
            <>
              <div className="checkbox-field">
                <input
                  type="checkbox"
                  id="opt_enabled"
                  checked={settings.optimization.enabled}
                  onChange={(e) => setField("optimization", "enabled", e.target.checked)}
                />
                <label htmlFor="opt_enabled">Enable HLS optimization</label>
              </div>
              <div className="settings-field">
                <label>Renditions (comma separated)</label>
                <input
                  value={settings.optimization.renditions.join(", ")}
                  onChange={(e) =>
                    setField(
                      "optimization",
                      "renditions",
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    )
                  }
                />
              </div>
              <div className="settings-field">
                <label>Segment Length (seconds)</label>
                <input
                  type="number"
                  value={settings.optimization.segment_seconds}
                  onChange={(e) => setField("optimization", "segment_seconds", Number(e.target.value))}
                />
              </div>
              <div className="settings-field">
                <label>Video Codec</label>
                <select
                  value={settings.optimization.video_codec}
                  onChange={(e) => setField("optimization", "video_codec", e.target.value)}
                >
                  {["libx264", "libx265", "libvpx-vp9", "libaom-av1"].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="settings-field">
                <label>CRF</label>
                <input
                  type="number"
                  min={0}
                  max={51}
                  value={settings.optimization.crf}
                  onChange={(e) => setField("optimization", "crf", Number(e.target.value))}
                />
                <div className="hint">Lower = better quality, larger files</div>
              </div>
              <div className="settings-field">
                <label>Preset</label>
                <select
                  value={settings.optimization.preset}
                  onChange={(e) => setField("optimization", "preset", e.target.value)}
                >
                  {["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"].map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
            </>
          )}

          {section === "providers" && (
            <>
              <div className="settings-field">
                <label>TMDB API Key</label>
                <input
                  value={keyValue(settings.providers.tmdb.api_key).display}
                  placeholder={keyValue(settings.providers.tmdb.api_key).isMasked ? "Configured (saved from .env)" : "Paste your TMDB key"}
                  onChange={(e) => setField("providers", "tmdb", { api_key: e.target.value })}
                />
                <div className="hint">Themoviedb.org — movie/show metadata</div>
              </div>
              <div className="settings-field">
                <label>FanArt.tv API Key</label>
                <input
                  value={keyValue(settings.providers.fanart.api_key).display}
                  placeholder={keyValue(settings.providers.fanart.api_key).isMasked ? "Configured (saved from .env)" : "Paste your FanArt key"}
                  onChange={(e) => setField("providers", "fanart", { api_key: e.target.value })}
                />
                <div className="hint">fanart.tv — posters, backdrops, logos</div>
              </div>
              <div className="checkbox-field">
                <input
                  type="checkbox"
                  id="os_enabled"
                  checked={settings.providers.opensubtitles.enabled}
                  onChange={(e) => setField("providers", "opensubtitles", { enabled: e.target.checked })}
                />
                <label htmlFor="os_enabled">Enable OpenSubtitles</label>
              </div>
              <div className="settings-field">
                <label>OpenSubtitles API Key</label>
                <input
                  value={keyValue(settings.providers.opensubtitles.api_key).display}
                  placeholder={keyValue(settings.providers.opensubtitles.api_key).isMasked ? "Configured (saved from .env)" : "Paste your OpenSubtitles key"}
                  onChange={(e) => setField("providers", "opensubtitles", { api_key: e.target.value })}
                />
              </div>
              <div className="settings-field">
                <label>Subtitle Languages (comma separated)</label>
                <input
                  value={settings.providers.opensubtitles.languages.join(", ")}
                  onChange={(e) =>
                    setField(
                      "providers",
                      "opensubtitles",
                      { languages: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) },
                    )
                  }
                />
              </div>
              <p className="panel-desc">Provider keys are also read from the .env file at startup.</p>
            </>
          )}

          <div className="settings-actions">
            <button className="btn btn-primary" onClick={save}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>

      {showAddLib && (
        <div className="modal-backdrop" onClick={() => setShowAddLib(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Add Library</h3>
            <div className="form-field">
              <label>Name</label>
              <input
                value={newLib.name}
                onChange={(e) => setNewLib({ ...newLib, name: e.target.value })}
                placeholder="e.g. Movies"
                autoFocus
              />
            </div>
            <div className="form-field">
              <label>Path</label>
              <input
                value={newLib.path}
                onChange={(e) => setNewLib({ ...newLib, path: e.target.value })}
                placeholder="./media/movies or C:/media/movies"
              />
            </div>
            <div className="form-field">
              <label>Type</label>
              <select value={newLib.type} onChange={(e) => setNewLib({ ...newLib, type: e.target.value })}>
                <option value="movie">Movie library</option>
                <option value="show">TV Show library</option>
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setShowAddLib(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={addLibrary}>
                <FolderIcon /> Add
              </button>
            </div>
          </div>
        </div>
      )}

      {showRestartConfirm && (
        <div className="modal-backdrop" onClick={() => setShowRestartConfirm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Restart Server?</h3>
            <p className="modal-warning">
              Restarting the server will interrupt any active streams, transcodes, and
              optimizations. The server will come back online automatically within a few
              seconds. Continue?
            </p>
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setShowRestartConfirm(false)}>Cancel</button>
              <button className="btn btn-primary btn-danger" onClick={restartServer} disabled={restarting}>
                <RestartIcon /> {restarting ? "Restarting..." : "Restart Now"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
