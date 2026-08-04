import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Hls from "hls.js";
import { api, streamUrl } from "../api";
import type { Item, Metadata, SubtitleTrack } from "../types";
import { CaptionIcon, CloseIcon, PlayIcon } from "../icons";
import "./Player.css";

interface PlayerProps {
  item: Item;
  onClose: () => void;
}

interface HlsLevel {
  index: number;
  height: number;
  width: number;
  bitrate: number;
}

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];
const STANDARD_HEIGHTS = [2160, 1440, 1080, 720, 480, 360, 240];

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return "0:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

interface SubtitleCue {
  start: number;
  end: number;
  text: string;
}

function parseVTT(vttText: string): SubtitleCue[] {
  const lines = vttText.split(/\r?\n/);
  const cues: SubtitleCue[] = [];
  let currentStart = -1;
  let currentEnd = -1;
  let currentText: string[] = [];

  const timeToSec = (str: string): number => {
    const parts = str.trim().replace(',', '.').split(':');
    if (parts.length === 3) {
      return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
    } else if (parts.length === 2) {
      return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
    }
    return 0;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.includes('-->')) {
      if (currentStart >= 0 && currentText.length > 0) {
        cues.push({
          start: currentStart,
          end: currentEnd,
          text: currentText.join('\n').replace(/<[^>]*>/g, ''),
        });
        currentText = [];
      }
      const [startStr, endStr] = line.split('-->');
      currentStart = timeToSec(startStr);
      currentEnd = timeToSec(endStr.trim().split(' ')[0]);
    } else if (currentStart >= 0 && line.length > 0 && !line.startsWith('WEBVTT') && !line.startsWith('NOTE')) {
      currentText.push(line);
    } else if (line.length === 0 && currentStart >= 0) {
      if (currentText.length > 0) {
        cues.push({
          start: currentStart,
          end: currentEnd,
          text: currentText.join('\n').replace(/<[^>]*>/g, ''),
        });
        currentText = [];
        currentStart = -1;
      }
    }
  }
  if (currentStart >= 0 && currentText.length > 0) {
    cues.push({
      start: currentStart,
      end: currentEnd,
      text: currentText.join('\n').replace(/<[^>]*>/g, ''),
    });
  }
  return cues;
}

function getQualityLabel(height: number, width?: number): string {
  if (height >= 1600 || (width && width >= 3500)) return "4K";
  if (height >= 1440) return "1440p";
  if (height >= 1080) return "1080p";
  if (height >= 720) return "720p";
  if (height >= 480) return "480p";
  return `${height}p`;
}

export function Player({ item, onClose }: PlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hlsRef = useRef<Hls | null>(null);

  const [meta, setMeta] = useState<Metadata | null>(item.metadata ?? null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [buffered, setBuffered] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [hlsLevels, setHlsLevels] = useState<HlsLevel[]>([]);
  const isDirectPlayable = meta?.playback?.direct_play_supported ?? (item.metadata?.playback?.direct_play_supported ?? false);
  const [currentQuality, setCurrentQuality] = useState<string>(() => isDirectPlayable ? "direct" : "hls-original");
  const [subtitleTracks, setSubtitleTracks] = useState<SubtitleTrack[]>([]);
  const [activeSubtitle, setActiveSubtitle] = useState<number | null>(null);
  const [subtitleCues, setSubtitleCues] = useState<SubtitleCue[]>([]);
  const [subtitleDelay, setSubtitleDelay] = useState<number>(0);
  const [subtitleSize, setSubtitleSize] = useState<number>(() => {
    const saved = localStorage.getItem("quark_sub_size");
    return saved ? Number(saved) : 22;
  });
  const [subtitleBg, setSubtitleBg] = useState<boolean>(() => {
    const saved = localStorage.getItem("quark_sub_bg");
    return saved !== null ? saved === "true" : true;
  });
  const [searchingOS, setSearchingOS] = useState(false);

  // Sync settings with backend
  useEffect(() => {
    api
      .settings()
      .then((st) => {
        if (st.streaming?.subtitle_size) setSubtitleSize(st.streaming.subtitle_size);
        if (st.streaming?.subtitle_bg !== undefined) setSubtitleBg(st.streaming.subtitle_bg);
      })
      .catch(() => {});
  }, []);

  const changeSubtitleSize = (size: number) => {
    setSubtitleSize(size);
    localStorage.setItem("quark_sub_size", String(size));
    api
      .settings()
      .then((st) => {
        api.saveSettings({ streaming: { ...st.streaming, subtitle_size: size } }).catch(() => {});
      })
      .catch(() => {});
  };

  const changeSubtitleBg = (bg: boolean) => {
    setSubtitleBg(bg);
    localStorage.setItem("quark_sub_bg", String(bg));
    api
      .settings()
      .then((st) => {
        api.saveSettings({ streaming: { ...st.streaming, subtitle_bg: bg } }).catch(() => {});
      })
      .catch(() => {});
  };
  const [menuOpen, setMenuOpen] = useState<"speed" | "quality" | "subtitles" | null>(null);
  const [loading, setLoading] = useState(true);
  const [seekFlash, setSeekFlash] = useState<{ delta: number; id: number } | null>(null);

  const controlsTimer = useRef<number | undefined>(undefined);
  const flashTimer = useRef<number | undefined>(undefined);
  const savedPosition = useRef<number>(0);

  // Fetch and parse WebVTT cues for smooth Montserrat subtitle engine
  useEffect(() => {
    if (activeSubtitle === null) {
      setSubtitleCues([]);
      return;
    }
    const url = `/api/items/${item.media_id}/subtitles/${activeSubtitle}`;
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("Subtitle not ready");
        return res.text();
      })
      .then((text) => setSubtitleCues(parseVTT(text)))
      .catch(() => setSubtitleCues([]));
  }, [item.media_id, activeSubtitle]);
  useEffect(() => {
    api
      .item(item.media_id)
      .then((d) => {
        if (d.metadata) {
          setMeta(d.metadata);
          setSubtitleTracks(d.metadata.subtitles ?? []);
          const def = d.metadata.subtitles?.find((s) => s.default);
          if (def) setActiveSubtitle(def.index ?? null);
          if (d.metadata.playback?.direct_play_supported === false) {
            setCurrentQuality((prev) => (prev === "direct" ? "hls-original" : prev));
          }
        }
      })
      .catch(() => {});
  }, [item.media_id]);

  // Load saved position
  useEffect(() => {
    api.state(item.media_id).then((st) => {
      if (st.position > 2 && st.duration > 0 && st.position < st.duration - 10) {
        savedPosition.current = st.position;
      }
    });
  }, [item.media_id]);

  // Initialize playback stream based on chosen quality selection
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setError(null);
    setLoading(true);

    let srcUrl = "";
    let isHls = false;
    let targetHlsLevel = -1;

    if (currentQuality === "direct") {
      srcUrl = streamUrl(item.media_id, "direct");
      isHls = !meta?.playback?.direct_play_supported || item.optimized;
    } else if (currentQuality === "hls-original") {
      const startPos = savedPosition.current > 0 ? `&start=${savedPosition.current}` : "";
      srcUrl = `${streamUrl(item.media_id, "transcode")}&height=${sourceHeight}&original=true${startPos}`;
      isHls = true;
      targetHlsLevel = -1;
    } else if (currentQuality === "auto") {
      srcUrl = streamUrl(item.media_id, "auto");
      isHls = !meta?.playback?.direct_play_supported || item.optimized;
    } else if (currentQuality.startsWith("res-")) {
      const targetHeight = Number(currentQuality.replace("res-", ""));
      if (item.optimized && hlsLevels.length > 0) {
        const matchIdx = hlsLevels.findIndex((l) => l.height === targetHeight);
        if (matchIdx !== -1) {
          srcUrl = streamUrl(item.media_id, "hls");
          isHls = true;
          targetHlsLevel = matchIdx;
        } else {
          const startPos = savedPosition.current > 0 ? `&start=${savedPosition.current}` : "";
          srcUrl = `${streamUrl(item.media_id, "transcode")}&height=${targetHeight}${startPos}`;
          isHls = true;
        }
      } else {
        const startPos = savedPosition.current > 0 ? `&start=${savedPosition.current}` : "";
        srcUrl = `${streamUrl(item.media_id, "transcode")}&height=${targetHeight}${startPos}`;
        isHls = true;
      }
    }

    const startHls = (src: string) => {
      if (hlsRef.current) hlsRef.current.destroy();
      if (Hls.isSupported()) {
        const hls = new Hls({ enableWorker: true });
        hlsRef.current = hls;
        hls.loadSource(src);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          if (targetHlsLevel >= 0) {
            hls.currentLevel = targetHlsLevel;
          }
          const levels = hls.levels.map((l, index) => ({
            index,
            height: l.height,
            width: l.width,
            bitrate: l.bitrate,
          }));
          if (levels.length > 0) setHlsLevels(levels);
          video.play().catch(() => {});
        });
        hls.on(Hls.Events.ERROR, (_evt, data) => {
          if (data.fatal) setError(`Playback error: ${data.type}`);
        });
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = src;
        video.play().catch(() => {});
      } else {
        setError("HLS is not supported in this browser");
      }
    };

    if (isHls) {
      startHls(srcUrl);
    } else {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      video.src = srcUrl;
      video.play().catch(() => {});
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [item.media_id, item.optimized, currentQuality]);

  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    setDuration(video.duration);
    setLoading(false);
    if (savedPosition.current > 0) {
      video.currentTime = savedPosition.current;
      savedPosition.current = 0;
    }
  }, []);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) video.play();
    else video.pause();
  };

  const flashSeek = (delta: number) => {
    setSeekFlash({ delta, id: Date.now() });
    window.clearTimeout(flashTimer.current);
    flashTimer.current = window.setTimeout(() => setSeekFlash(null), 700);
  };

  const seekBy = (delta: number) => {
    const video = videoRef.current;
    if (!video) return;
    const next = Math.max(0, Math.min(video.duration || 0, video.currentTime + delta));
    video.currentTime = next;
    setCurrentTime(next);
    flashSeek(delta);
  };

  const seekTo = (value: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = value;
    setCurrentTime(value);
  };

  const changeRate = (rate: number) => {
    const video = videoRef.current;
    if (video) video.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const selectQuality = (qualKey: string) => {
    const video = videoRef.current;
    if (video && video.currentTime > 0) {
      savedPosition.current = video.currentTime;
      saveCurrentProgress();
    }
    setCurrentQuality(qualKey);
    setMenuOpen(null);
    if (qualKey.startsWith("hls-") && hlsRef.current) {
      const idx = Number(qualKey.replace("hls-", ""));
      hlsRef.current.currentLevel = idx;
    }
  };

  const selectSubtitle = (trackIndex: number | null) => {
    const video = videoRef.current;
    if (!video) return;
    const tracks = video.textTracks;
    for (let i = 0; i < tracks.length; i++) {
      const track = tracks[i];
      if (track.kind === "subtitles") {
        track.mode = "disabled";
      }
    }
    setActiveSubtitle(trackIndex);
    setMenuOpen(null);
  };

  const handleDownloadOpenSubtitles = async () => {
    if (searchingOS) return;
    setSearchingOS(true);
    try {
      await api.downloadSubtitles(item.media_id);
      setTimeout(async () => {
        const d = await api.item(item.media_id);
        if (d.metadata?.subtitles) {
          setSubtitleTracks(d.metadata.subtitles);
        }
        setSearchingOS(false);
      }, 3000);
    } catch {
      setSearchingOS(false);
    }
  };

  const showControlsTemporarily = () => {
    setShowControls(true);
    window.clearTimeout(controlsTimer.current);
    controlsTimer.current = window.setTimeout(() => {
      if (!menuOpen) setShowControls(false);
    }, 1800);
  };

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current?.requestFullscreen();
    }
  };

  useEffect(() => {
    const onFsChange = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  const saveCurrentProgress = useCallback(() => {
    const video = videoRef.current;
    if (video && video.duration > 0 && video.currentTime > 1) {
      api.progress(item.media_id, video.currentTime, video.duration);
    }
  }, [item.media_id]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const onTime = () => setCurrentTime(video.currentTime);
    const onProgress = () => {
      if (video.buffered.length > 0) setBuffered(video.buffered.end(video.buffered.length - 1));
    };
    const onEnded = () => {
      setPlaying(false);
      api.progress(item.media_id, video.duration, video.duration);
    };
    const onPlay = () => setPlaying(true);
    const onPause = () => {
      setPlaying(false);
      saveCurrentProgress();
    };
    const onSeeked = () => saveCurrentProgress();
    const onVol = () => {
      setVolume(video.volume);
      setMuted(video.muted);
    };
    video.addEventListener("timeupdate", onTime);
    video.addEventListener("progress", onProgress);
    video.addEventListener("ended", onEnded);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("seeked", onSeeked);
    video.addEventListener("volumechange", onVol);
    return () => {
      video.removeEventListener("timeupdate", onTime);
      video.removeEventListener("progress", onProgress);
      video.removeEventListener("ended", onEnded);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("seeked", onSeeked);
      video.removeEventListener("volumechange", onVol);
    };
  }, [item.media_id, saveCurrentProgress]);

  // Frequent precise progress saving (every 2s) + on unload
  useEffect(() => {
    const timer = window.setInterval(() => {
      saveCurrentProgress();
    }, 2000);

    const onUnload = () => saveCurrentProgress();
    window.addEventListener("beforeunload", onUnload);

    return () => {
      window.clearInterval(timer);
      window.removeEventListener("beforeunload", onUnload);
      saveCurrentProgress();
    };
  }, [saveCurrentProgress]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.volume = volume;
    video.muted = muted;
  }, [volume, muted]);

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key) {
        case " ":
        case "k":
        case "K":
          e.preventDefault();
          togglePlay();
          break;
        case "ArrowLeft":
        case "j":
        case "J":
          e.preventDefault();
          seekBy(-10);
          break;
        case "ArrowRight":
        case "l":
        case "L":
          e.preventDefault();
          seekBy(10);
          break;
        case "ArrowUp":
          e.preventDefault();
          setVolume((v) => Math.min(1, Math.round((v + 0.1) * 10) / 10));
          break;
        case "ArrowDown":
          e.preventDefault();
          setVolume((v) => Math.max(0, Math.round((v - 0.1) * 10) / 10));
          break;
        case "m":
        case "M":
          setMuted((m) => !m);
          break;
        case "f":
        case "F":
          toggleFullscreen();
          break;
        case "Escape":
          if (document.fullscreenElement) document.exitFullscreen();
          else onClose();
          break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onClose]);

  const totalDuration = useMemo(() => {
    const fileDur = meta?.files?.[0]?.duration;
    if (fileDur && isFinite(fileDur) && fileDur > 0) {
      return fileDur;
    }
    if (meta?.runtime && isFinite(meta.runtime) && meta.runtime > 0) {
      return meta.runtime * 60;
    }
    if (isFinite(duration) && duration > 30) {
      return duration;
    }
    return duration || 0;
  }, [duration, meta]);

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;
  const chunkBuffered = isFinite(duration) && duration > 0 ? duration : buffered;
  const bufferedPct = totalDuration > 0 ? Math.min(100, (Math.max(buffered, chunkBuffered) / totalDuration) * 100) : 0;

  const sourceHeight = meta?.video?.height ?? 1080;
  const sourceWidth = meta?.video?.width ?? 1920;
  const availableHeights = useMemo(() => {
    const filtered = STANDARD_HEIGHTS.filter((h) => h <= sourceHeight);
    if (!filtered.includes(sourceHeight)) {
      filtered.unshift(sourceHeight);
    }
    return filtered.sort((a, b) => b - a);
  }, [sourceHeight]);

  const effectiveTime = currentTime + subtitleDelay;
  const activeCueText = useMemo(() => {
    if (activeSubtitle === null || subtitleCues.length === 0) return "";
    const activeCues = subtitleCues.filter(
      (c) => effectiveTime >= c.start && effectiveTime <= c.end
    );
    return activeCues.map((c) => c.text).join("\n");
  }, [activeSubtitle, subtitleCues, effectiveTime]);

  const qualityOptions = useMemo(() => {
    const opts: { id: string; label: string }[] = [];
    if (isDirectPlayable) {
      opts.push({ id: "direct", label: `Original (Direct)` });
    }
    opts.push({ id: "hls-original", label: `Original HLS (${getQualityLabel(sourceHeight, sourceWidth)})` });
    opts.push({ id: "auto", label: "Auto (HLS)" });
    for (const h of availableHeights) {
      if (h < sourceHeight) {
        opts.push({
          id: `res-${h}`,
          label: `${getQualityLabel(h)}`,
        });
      }
    }
    return opts;
  }, [isDirectPlayable, sourceHeight, sourceWidth, availableHeights]);

  return (
    <div
      className={`player ${!showControls ? "hide-cursor" : ""}`}
      ref={containerRef}
      onMouseMove={showControlsTemporarily}
      onClick={() => setMenuOpen(null)}
    >
      <video
        ref={videoRef}
        onLoadedMetadata={handleLoadedMetadata}
        onError={() => setError("Unable to play video file")}
        className="player-video"
        crossOrigin="anonymous"
        onClick={(e) => {
          e.stopPropagation();
          togglePlay();
        }}
      />

      {activeSubtitle !== null && activeCueText && (
        <div className={`subtitle-overlay ${showControls ? "with-controls" : ""}`}>
          <div className={`subtitle-text ${subtitleBg ? "with-bg" : ""}`} style={{ fontSize: `${subtitleSize}px` }}>
            {activeCueText}
          </div>
        </div>
      )}

      {loading && (
        <div className="player-loading">
          <div className="player-spinner" />
        </div>
      )}

      {seekFlash && (
        <div key={seekFlash.id} className={`seek-flash ${seekFlash.delta > 0 ? "forward" : "back"}`}>
          {seekFlash.delta > 0 ? "»" : "«"} {Math.abs(seekFlash.delta)}s
        </div>
      )}

      {error && (
        <div className="player-error">
          <p>{error}</p>
          <button className="btn btn-ghost" onClick={() => setError(null)}>
            Retry
          </button>
        </div>
      )}

      <div className={`player-controls ${showControls ? "visible" : ""}`} onClick={(e) => e.stopPropagation()}>
        <div className="player-top">
          <div className="player-title-block">
            <div className="player-title">{item.series_title || item.display_title || item.title}</div>
            {item.kind === "episode" && (
              <div className="player-subtitle">
                {item.season != null && item.episode != null ? `S${String(item.season).padStart(2, "0")}E${String(item.episode).padStart(2, "0")}` : ""}
                {(meta?.title || item.title) && (item.series_title || item.display_title) ? ` · ${meta?.title || item.title}` : ""}
              </div>
            )}
          </div>
          <button className="player-close-btn" onClick={onClose} title="Close (Esc)">
            <CloseIcon />
          </button>
        </div>

        <div className="player-center" onClick={togglePlay}>
          {!playing && (
            <div className="play-center-btn">
              <PlayIcon />
            </div>
          )}
        </div>

        <div className="player-bottom-panel">
          <div
            className="player-timeline"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const pct = (e.clientX - rect.left) / rect.width;
              seekTo(pct * totalDuration);
            }}
          >
            <div className="timeline-bg" />
            <div className="timeline-buffered" style={{ width: `${bufferedPct}%` }} />
            <div className="timeline-progress" style={{ width: `${progress}%` }} />
            <div className="timeline-thumb" style={{ left: `${progress}%` }} />
          </div>

          <div className="player-controls-bar">
            <div className="bar-left">
              <button className="btn-icon big-play" onClick={togglePlay} title={playing ? "Pause (Space)" : "Play (Space)"}>
                {playing ? (
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 4h4v16H6zM14 4h4v16h-4z" />
                  </svg>
                ) : (
                  <PlayIcon />
                )}
              </button>

              <button className="btn-icon" onClick={() => seekBy(-10)} title="Rewind 10s (←)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M8 12l4-4v3h5v2h-5v3l-4-4Z" strokeLinejoin="round" />
                  <path d="M12 5a7 7 0 1 1-6.6 9.5" strokeLinecap="round" />
                </svg>
                <span className="btn-tag">10</span>
              </button>

              <button className="btn-icon" onClick={() => seekBy(10)} title="Forward 10s (→)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M16 12l-4-4v3H7v2h5v3l4-4Z" strokeLinejoin="round" />
                  <path d="M12 5a7 7 0 1 0 6.6 9.5" strokeLinecap="round" />
                </svg>
                <span className="btn-tag">10</span>
              </button>

              <div className="volume-group">
                <button className="btn-icon" onClick={() => setMuted(!muted)} title="Mute (M)">
                  {muted || volume === 0 ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M11 5 6 9H3v6h3l5 4V5Z" strokeLinejoin="round" />
                      <path d="m16 9 5 6M21 9l-5 6" strokeLinecap="round" />
                    </svg>
                  ) : volume < 0.5 ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M11 5 6 9H3v6h3l5 4V5Z" strokeLinejoin="round" />
                      <path d="M15.5 8.5a5 5 0 0 1 0 7" strokeLinecap="round" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M11 5 6 9H3v6h3l5 4V5Z" strokeLinejoin="round" />
                      <path d="M15.5 8.5a5 5 0 0 1 0 7M18 6a9 9 0 0 1 0 12" strokeLinecap="round" />
                    </svg>
                  )}
                </button>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={muted ? 0 : volume}
                  onChange={(e) => setVolume(Number(e.target.value))}
                  className="volume-slider"
                />
              </div>

              <div className="time-display">
                <span>{formatTime(currentTime)}</span>
                <span className="time-slash">/</span>
                <span>{formatTime(totalDuration)}</span>
              </div>
            </div>

            <div className="bar-right">
              {/* Speed Menu */}
              <div className="menu-wrap">
                <button
                  className={`btn-icon btn-text ${menuOpen === "speed" ? "active" : ""}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpen(menuOpen === "speed" ? null : "speed");
                  }}
                  title="Playback speed"
                >
                  {playbackRate === 1 ? "1x" : `${playbackRate}x`}
                </button>
                {menuOpen === "speed" && (
                  <div className="pop-menu">
                    <div className="pop-header">Speed</div>
                    {SPEEDS.map((sp) => (
                      <button
                        key={sp}
                        className={`pop-item ${playbackRate === sp ? "active" : ""}`}
                        onClick={() => {
                          changeRate(sp);
                          setMenuOpen(null);
                        }}
                      >
                        <span>{sp}x</span>
                        {playbackRate === sp && <span className="pop-check">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Quality Menu */}
              <div className="menu-wrap">
                <button
                  className={`btn-icon ${menuOpen === "quality" ? "active" : ""}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpen(menuOpen === "quality" ? null : "quality");
                  }}
                  title="Quality"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M3 8h18M6 12h12M9 16h6" strokeLinecap="round" />
                  </svg>
                </button>
                {menuOpen === "quality" && (
                  <div className="pop-menu">
                    <div className="pop-header">Quality</div>
                    {qualityOptions.map((q) => (
                      <button
                        key={q.id}
                        className={`pop-item ${currentQuality === q.id ? "active" : ""}`}
                        onClick={() => selectQuality(q.id)}
                      >
                        <span>{q.label}</span>
                        {currentQuality === q.id && <span className="pop-check">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Subtitles Menu */}
              <div className="menu-wrap">
                <button
                  className={`btn-icon ${activeSubtitle !== null ? "highlight" : ""} ${menuOpen === "subtitles" ? "active" : ""}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpen(menuOpen === "subtitles" ? null : "subtitles");
                  }}
                  title="Subtitles"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <rect x="2" y="5" width="20" height="14" rx="3" />
                    <path d="M8 10.5a2 2 0 0 1 2-2h1M8 13.5a2 2 0 0 0 2 2h1M16 10.5a2 2 0 0 0-2-2h-1M16 13.5a2 2 0 0 1-2 2h-1" strokeLinecap="round" />
                  </svg>
                </button>
                {menuOpen === "subtitles" && (
                  <div className="pop-menu" onClick={(e) => e.stopPropagation()}>
                    <div className="pop-header">Subtitles</div>

                    <div className="subtitle-delay-row">
                      <span className="delay-label">Size:</span>
                      <div className="delay-btns">
                        {[16, 22, 28, 34].map((sz) => (
                          <button
                            key={sz}
                            className={`delay-btn ${subtitleSize === sz ? "active-delay" : ""}`}
                            onClick={() => changeSubtitleSize(sz)}
                          >
                            {sz === 16 ? "S" : sz === 22 ? "M" : sz === 28 ? "L" : "XL"}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="subtitle-delay-row">
                      <span className="delay-label">Style:</span>
                      <button
                        className={`delay-btn ${subtitleBg ? "active-delay" : ""}`}
                        onClick={() => changeSubtitleBg(!subtitleBg)}
                      >
                        {subtitleBg ? "Blur Glass" : "No Background"}
                      </button>
                    </div>

                    <div className="subtitle-delay-row">
                      <span className="delay-label">Delay: <span className="delay-val">{subtitleDelay > 0 ? `+${subtitleDelay.toFixed(1)}s` : `${subtitleDelay.toFixed(1)}s`}</span></span>
                      <div className="delay-btns">
                        <button className="delay-btn" onClick={() => setSubtitleDelay((d) => Math.max(-5, Math.round((d - 0.5) * 10) / 10))}>-0.5s</button>
                        <button className="delay-btn" onClick={() => setSubtitleDelay(0)}>0s</button>
                        <button className="delay-btn" onClick={() => setSubtitleDelay((d) => Math.min(5, Math.round((d + 0.5) * 10) / 10))}>+0.5s</button>
                      </div>
                    </div>

                    <button
                      className={`pop-item ${activeSubtitle === null ? "active" : ""}`}
                      onClick={() => selectSubtitle(null)}
                    >
                      <span>Off</span>
                      {activeSubtitle === null && <span className="pop-check">✓</span>}
                    </button>
                    {subtitleTracks.map((tr) => (
                      <button
                        key={tr.index ?? tr.title}
                        className={`pop-item ${activeSubtitle === tr.index ? "active" : ""}`}
                        onClick={() => selectSubtitle(tr.index ?? null)}
                      >
                        <span>{tr.language?.toUpperCase() ?? tr.title ?? `Track ${(tr.index ?? 0) + 1}`}</span>
                        {activeSubtitle === tr.index && <span className="pop-check">✓</span>}
                      </button>
                    ))}

                    <button
                      className="os-fetch-btn"
                      onClick={handleDownloadOpenSubtitles}
                      disabled={searchingOS}
                    >
                      <CaptionIcon /> {searchingOS ? "Searching..." : "Search OpenSubtitles"}
                    </button>
                  </div>
                )}
              </div>

              {/* Fullscreen Button */}
              <button className="btn-icon" onClick={toggleFullscreen} title="Fullscreen (F)">
                {fullscreen ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" strokeLinecap="round" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
