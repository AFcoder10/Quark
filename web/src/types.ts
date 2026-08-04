export interface Library {
  id: string;
  name: string;
  path: string;
  type: "movie" | "show";
  enabled: boolean;
  path_resolved: string;
}

export interface VideoStream {
  codec?: string | null;
  width?: number | null;
  height?: number | null;
  bitrate?: number | null;
  fps?: number | null;
  profile?: string | null;
  pixel_format?: string | null;
}

export interface AudioTrack {
  index?: number | null;
  codec?: string | null;
  language?: string | null;
  channels?: number | null;
  sample_rate?: number | null;
  title?: string | null;
  profile?: string | null;
}

export interface SubtitleTrack {
  index?: number | null;
  codec?: string | null;
  language?: string | null;
  title?: string | null;
  forced?: boolean;
  default?: boolean;
  embedded?: boolean;
  format?: string | null;
  path?: string | null;
}

export interface Rendition {
  name: string;
  height: number;
  width: number;
  bitrate: number;
  playlist: string;
}

export interface Metadata {
  schema_version: number;
  media_id: string;
  kind: "movie" | "episode";
  library_id: string;
  title: string;
  original_title?: string | null;
  year?: number | null;
  tmdb_id?: number | null;
  imdb_id?: string | null;
  tvdb_id?: number | null;
  overview?: string | null;
  rating?: number | null;
  vote_count?: number | null;
  popularity?: number | null;
  genres?: string[];
  runtime?: number | null;
  season?: number | null;
  episode?: number | null;
  series_title?: string | null;
  series_id?: number | null;
  air_date?: string | null;
  first_air_date?: string | null;
  last_air_date?: string | null;
  status?: string | null;
  tagline?: string | null;
  certification?: string | null;
  networks?: string[];
  creators?: string[];
  production_companies?: string[];
  spoken_languages?: string[];
  number_of_seasons?: number | null;
  number_of_episodes?: number | null;
  files?: { path: string; duration?: number | null }[];
  primary_file: string;
  video?: VideoStream | null;
  audio?: AudioTrack[];
  subtitles?: SubtitleTrack[];
  artwork: Record<string, string>;
  optimization: { status: string; path?: string | null; renditions?: Rendition[] };
  playback: { direct_play_supported: boolean; mode: string; reason?: string | null };
}

export interface Item {
  media_id: string;
  kind: "movie" | "episode";
  library_id: string;
  title: string;
  series_title?: string | null;
  season?: number | null;
  episode?: number | null;
  year?: number | null;
  display_title: string;
  primary_file: string;
  has_metadata: boolean;
  optimized: boolean;
  artwork?: Record<string, string>;
  metadata?: Metadata;
}

export interface ShowEpisode {
  episode_number?: number | null;
  title?: string | null;
  overview?: string | null;
  air_date?: string | null;
  rating?: number | null;
  runtime?: number | null;
  still?: string | null;
  has_file: boolean;
  optimized: boolean;
  media_id?: string | null;
  local_title?: string | null;
}

export interface ShowSeason {
  season_number: number;
  name: string;
  episodes: ShowEpisode[];
}

export interface Show {
  series_title: string;
  tmdb_id?: number | null;
  year?: number | null;
  rating?: number | null;
  tagline?: string | null;
  status?: string | null;
  overview?: string | null;
  genres?: string[];
  networks?: string[];
  creators?: string[];
  first_air_date?: string | null;
  last_air_date?: string | null;
  number_of_seasons?: number | null;
  number_of_episodes?: number | null;
  episode_count?: number;
  artwork: Record<string, string>;
  artwork_urls?: Record<string, string>;
  seasons: ShowSeason[];
  episodes?: Item[];
}

export interface PlaybackState {
  position: number;
  duration: number;
  watched: boolean;
  last_played_at?: string | null;
}

export interface RecentState {
  media_id: string;
  position: number;
  duration: number;
  last_played_at?: string | null;
  progress_pct: number;
}

export interface ScanJob {
  job_id: string;
  library_id: string;
  status: string;
  error?: string | null;
  result: Record<string, number>;
  created_at: string;
  finished_at?: string | null;
}

export interface OptimizationStatus {
  status: string;
  media_id: string;
  progress: number;
  message?: string;
}

export interface Settings {
  server: { host: string; port: number; log_level: string; scan_on_startup: boolean };
  streaming: {
    default_mode: string;
    direct_play_codecs: string[];
    direct_play_containers: string[];
    live_transcode_height: number;
    live_idle_seconds: number;
    subtitle_size?: number;
    subtitle_bg?: boolean;
  };
  optimization: {
    enabled: boolean;
    renditions: string[];
    segment_seconds: number;
    video_codec: string;
    crf: number;
    preset: string;
    audio_copy_codecs: string[];
    subtitle_format: string;
  };
  providers: {
    tmdb: { api_key: string };
    fanart: { api_key: string };
    opensubtitles: { enabled: boolean; api_key: string; languages: string[] };
  };
}

export interface Health {
  status: string;
  version: string;
  platform: string;
  ffmpeg: boolean;
  ffprobe: boolean;
  mediainfo: boolean;
  libraries: number;
  items: number;
}
