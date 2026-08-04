import type {
  Health,
  Item,
  Library,
  Metadata,
  OptimizationStatus,
  PlaybackState,
  RecentState,
  ScanJob,
  Settings,
  Show,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/system/health"),

  libraries: () => request<Library[]>("/libraries"),
  addLibrary: (body: { name: string; path: string; type: string }) =>
    request<Library>("/libraries", { method: "POST", body: JSON.stringify(body) }),
  removeLibrary: (id: string) => request<{ status: string }>(`/libraries/${id}`, { method: "DELETE" }),
  scanLibrary: (id: string) => request<{ status: string; job_id: string }>(`/libraries/${id}/scan`, { method: "POST" }),
  scanAll: () => request<{ status: string; job_ids: string[] }>("/libraries/scan-all", { method: "POST" }),
  scanJobs: () => request<{ jobs: ScanJob[] }>("/libraries/scan/jobs"),

  items: (params?: { library_id?: string; kind?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.library_id) qs.set("library_id", params.library_id);
    if (params?.kind) qs.set("kind", params.kind);
    if (params?.search) qs.set("search", params.search);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<Item[]>(`/items${suffix}`);
  },
  item: (id: string) => request<Item>(`/items/${id}`),
  itemMetadata: (id: string) => request<Metadata>(`/items/${id}/metadata`),
  refreshItem: (id: string) => request<{ status: string }>(`/items/${id}/refresh`, { method: "POST" }),
  deleteItem: (id: string) => request<{ status: string }>(`/items/${id}`, { method: "DELETE" }),
  downloadSubtitles: (id: string) =>
    request<{ status: string }>(`/items/${id}/subtitles/download`, { method: "POST" }),

  optimize: (id: string, mode: "hls" | "hevc" = "hls") =>
    request<{ status: string; media_id: string }>(`/items/${id}/optimize?mode=${mode}`, { method: "POST" }),
  optimizeShow: (showId: string, mode: "hls" | "hevc" = "hls") =>
    request<{ status: string; count: number; total_episodes: number }>(`/shows/${showId}/optimize?mode=${mode}`, { method: "POST" }),
  optimizeSeason: (showId: string, seasonNum: number, mode: "hls" | "hevc" = "hls") =>
    request<{ status: string; count: number; total_episodes: number }>(`/shows/${showId}/seasons/${seasonNum}/optimize?mode=${mode}`, { method: "POST" }),
  cancelOptimize: (id: string) => request<{ status: string }>(`/items/${id}/optimize`, { method: "DELETE" }),
  optimizeStatus: (id: string) => request<OptimizationStatus>(`/items/${id}/optimize/status`),
  optimizeQueue: () => request<{ jobs: OptimizationStatus[] }>("/optimize/queue"),

  state: (id: string) => request<PlaybackState>(`/state/${id}`),
  watched: () => request<{ items: Record<string, PlaybackState> }>("/state/watched"),
  recent: () => request<RecentState[]>("/state/recent"),
  markWatched: (id: string, watched = true) =>
    request<PlaybackState>(`/state/${id}/watch`, { method: "POST", body: JSON.stringify({ watched }) }),
  progress: (id: string, position: number, duration: number) =>
    request<PlaybackState>(`/state/${id}/progress`, {
      method: "POST",
      body: JSON.stringify({ position, duration }),
    }),

  settings: () => request<Settings>("/system/settings"),
  saveSettings: (body: Partial<Settings>) => request<Settings>("/system/settings", { method: "PUT", body: JSON.stringify(body) }),

  shows: () => request<Show[]>("/shows"),
  show: (title: string) => request<Show>(`/shows/${encodeURIComponent(title)}`),
};

export function streamUrl(id: string, mode?: string): string {
  const qs = mode ? `?mode=${mode}` : "";
  return `/api/items/${id}/stream${qs}`;
}

export function artworkUrl(id: string, name: string): string {
  return `/api/items/${id}/artwork/${name}`;
}
