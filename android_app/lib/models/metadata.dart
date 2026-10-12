class Artwork {
  final String? poster;
  final String? backdrop;
  final String? logo;
  final String? clearlogo;
  final String? clearart;
  final String? banner;
  final String? landscape;
  final String? thumb;
  final String? still;

  const Artwork({
    this.poster,
    this.backdrop,
    this.logo,
    this.clearlogo,
    this.clearart,
    this.banner,
    this.landscape,
    this.thumb,
    this.still,
  });

  factory Artwork.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const Artwork();
    return Artwork(
      poster: json['poster'] as String?,
      backdrop: json['backdrop'] as String?,
      logo: json['logo'] as String?,
      clearlogo: json['clearlogo'] as String?,
      clearart: json['clearart'] as String?,
      banner: json['banner'] as String?,
      landscape: json['landscape'] as String?,
      thumb: json['thumb'] as String?,
      still: json['still'] as String?,
    );
  }
}

class VideoInfo {
  final String? codec;
  final int? width;
  final int? height;
  final int? bitrate;
  final double? fps;
  final String? profile;
  final String? colorSpace;

  const VideoInfo({
    this.codec,
    this.width,
    this.height,
    this.bitrate,
    this.fps,
    this.profile,
    this.colorSpace,
  });

  factory VideoInfo.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const VideoInfo();
    return VideoInfo(
      codec: json['codec'] as String?,
      width: (json['width'] as num?)?.toInt(),
      height: (json['height'] as num?)?.toInt(),
      bitrate: (json['bitrate'] as num?)?.toInt(),
      fps: (json['fps'] as num?)?.toDouble(),
      profile: json['profile'] as String?,
      colorSpace: json['color_space'] as String?,
    );
  }

  bool get isHdr => (colorSpace ?? '').isNotEmpty && colorSpace!.toLowerCase().contains('bt2020');
}

class AudioTrack {
  final int? index;
  final String? codec;
  final String? language;
  final int? channels;
  final String? title;

  const AudioTrack({this.index, this.codec, this.language, this.channels, this.title});

  factory AudioTrack.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const AudioTrack();
    return AudioTrack(
      index: (json['index'] as num?)?.toInt(),
      codec: json['codec'] as String?,
      language: json['language'] as String?,
      channels: (json['channels'] as num?)?.toInt(),
      title: json['title'] as String?,
    );
  }

  String get label {
    final base = language ?? 'und';
    if (channels != null) {
      return '$base · $channels ch';
    }
    return base;
  }
}

class SubtitleTrack {
  final int? index;
  final String? codec;
  final String? language;
  final String? title;
  final bool forced;
  final bool isDefault;
  final bool embedded;
  final String? path;

  const SubtitleTrack({
    this.index,
    this.codec,
    this.language,
    this.title,
    this.forced = false,
    this.isDefault = false,
    this.embedded = true,
    this.path,
  });

  factory SubtitleTrack.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const SubtitleTrack();
    return SubtitleTrack(
      index: (json['index'] as num?)?.toInt(),
      codec: json['codec'] as String?,
      language: json['language'] as String?,
      title: json['title'] as String?,
      forced: json['forced'] as bool? ?? false,
      isDefault: json['default'] as bool? ?? false,
      embedded: json['embedded'] as bool? ?? true,
      path: json['path'] as String?,
    );
  }

  String get label => title ?? language ?? 'Subtitle';
}

class Rendition {
  final String name;
  final int height;
  final int width;
  final int bitrate;

  const Rendition({required this.name, required this.height, required this.width, required this.bitrate});

  factory Rendition.fromJson(Map<String, dynamic>? json) {
    return Rendition(
      name: json?['name'] as String? ?? '',
      height: (json?['height'] as num?)?.toInt() ?? 0,
      width: (json?['width'] as num?)?.toInt() ?? 0,
      bitrate: (json?['bitrate'] as num?)?.toInt() ?? 0,
    );
  }
}

class OptimizationInfo {
  final String status;
  final bool enabled;
  final String? path;
  final double progress;
  final String? error;
  final List<Rendition> renditions;

  const OptimizationInfo({
    this.status = 'none',
    this.enabled = true,
    this.path,
    this.progress = 0,
    this.error,
    this.renditions = const [],
  });

  factory OptimizationInfo.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const OptimizationInfo();
    return OptimizationInfo(
      status: json['status'] as String? ?? 'none',
      enabled: json['enabled'] as bool? ?? true,
      path: json['path'] as String?,
      progress: (json['progress'] as num?)?.toDouble() ?? 0,
      error: json['error'] as String?,
      renditions: (json['renditions'] as List?)
              ?.map((e) => Rendition.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }

  bool get isDone => status == 'done' && path != null;
  int get maxHeight =>
      renditions.fold<int>(0, (max, r) => r.height > max ? r.height : max);
}

class PlaybackInfo {
  final String? mode;
  final bool directPlaySupported;
  final String reason;

  const PlaybackInfo({this.mode, this.directPlaySupported = false, this.reason = ''});

  factory PlaybackInfo.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const PlaybackInfo();
    return PlaybackInfo(
      mode: json['mode'] as String?,
      directPlaySupported: json['direct_play_supported'] as bool? ?? false,
      reason: json['reason'] as String? ?? '',
    );
  }
}

class Metadata {
  final String mediaId;
  final String kind;
  final String title;
  final int? year;
  final int? tmdbId;
  final String? overview;
  final double? rating;
  final List<String> genres;
  final int? runtime;
  final int? season;
  final int? episode;
  final String? seriesTitle;
  final String? airDate;
  final String? firstAirDate;
  final String? status;
  final String? tagline;
  final List<String> networks;
  final List<String> creators;
  final int? numberOFSeasons;
  final int? numberOFEpisodes;
  final String primaryFile;
  final VideoInfo video;
  final List<AudioTrack> audio;
  final List<SubtitleTrack> subtitles;
  final Artwork artwork;
  final OptimizationInfo optimization;
  final PlaybackInfo playback;
  final String? createdAt;

  const Metadata({
    this.mediaId = '',
    this.kind = 'movie',
    this.title = '',
    this.year,
    this.tmdbId,
    this.overview,
    this.rating,
    this.genres = const [],
    this.runtime,
    this.season,
    this.episode,
    this.seriesTitle,
    this.airDate,
    this.firstAirDate,
    this.status,
    this.tagline,
    this.networks = const [],
    this.creators = const [],
    this.numberOFSeasons,
    this.numberOFEpisodes,
    this.primaryFile = '',
    this.video = const VideoInfo(),
    this.audio = const [],
    this.subtitles = const [],
    this.artwork = const Artwork(),
    this.optimization = const OptimizationInfo(),
    this.playback = const PlaybackInfo(),
    this.createdAt,
  });

  factory Metadata.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const Metadata();
    return Metadata(
      mediaId: json['media_id'] as String? ?? '',
      kind: json['kind'] as String? ?? 'movie',
      title: json['title'] as String? ?? '',
      year: (json['year'] as num?)?.toInt(),
      tmdbId: (json['tmdb_id'] as num?)?.toInt(),
      overview: json['overview'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
      genres: (json['genres'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      runtime: (json['runtime'] as num?)?.toInt(),
      season: (json['season'] as num?)?.toInt(),
      episode: (json['episode'] as num?)?.toInt(),
      seriesTitle: json['series_title'] as String?,
      airDate: json['air_date'] as String?,
      firstAirDate: json['first_air_date'] as String?,
      status: json['status'] as String?,
      tagline: json['tagline'] as String?,
      networks: (json['networks'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      creators: (json['creators'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      numberOFSeasons: (json['number_of_seasons'] as num?)?.toInt(),
      numberOFEpisodes: (json['number_of_episodes'] as num?)?.toInt(),
      primaryFile: json['primary_file'] as String? ?? '',
      video: VideoInfo.fromJson(json['video'] as Map<String, dynamic>?),
      audio: (json['audio'] as List?)
              ?.map((e) => AudioTrack.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      subtitles: (json['subtitles'] as List?)
              ?.map((e) => SubtitleTrack.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      artwork: Artwork.fromJson(json['artwork'] as Map<String, dynamic>?),
      optimization: OptimizationInfo.fromJson(json['optimization'] as Map<String, dynamic>?),
      playback: PlaybackInfo.fromJson(json['playback'] as Map<String, dynamic>?),
      createdAt: json['created_at'] as String?,
    );
  }
}
