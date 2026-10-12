import 'metadata.dart';

class ShowEpisodeLight {
  final String mediaId;
  final int? episode;
  final String title;
  final bool optimized;

  const ShowEpisodeLight({
    this.mediaId = '',
    this.episode,
    this.title = '',
    this.optimized = false,
  });

  factory ShowEpisodeLight.fromJson(Map<String, dynamic> json) {
    return ShowEpisodeLight(
      mediaId: json['media_id'] as String? ?? '',
      episode: (json['episode'] as num?)?.toInt(),
      title: json['title'] as String? ?? '',
      optimized: json['optimized'] as bool? ?? false,
    );
  }
}

class Show {
  final String seriesTitle;
  final int? tmdbId;
  final int? year;
  final double? rating;
  final String? overview;
  final List<String> genres;
  final int episodeCount;
  final Artwork artwork;
  final ArtworkUrls artworkUrls;
  final List<ShowEpisodeLight> episodes;

  const Show({
    this.seriesTitle = '',
    this.tmdbId,
    this.year,
    this.rating,
    this.overview,
    this.genres = const [],
    this.episodeCount = 0,
    this.artwork = const Artwork(),
    this.artworkUrls = const ArtworkUrls(),
    this.episodes = const [],
  });

  factory Show.fromJson(Map<String, dynamic> json) {
    return Show(
      seriesTitle: json['series_title'] as String? ?? '',
      tmdbId: (json['tmdb_id'] as num?)?.toInt(),
      year: (json['year'] as num?)?.toInt(),
      rating: (json['rating'] as num?)?.toDouble(),
      overview: json['overview'] as String?,
      genres: (json['genres'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      episodeCount: (json['episode_count'] as num?)?.toInt() ?? 0,
      artwork: Artwork.fromJson(json['artwork'] as Map<String, dynamic>?),
      artworkUrls: ArtworkUrls.fromJson(json['artwork_urls'] as Map<String, dynamic>?),
      episodes: (json['episodes'] as List?)
              ?.map((e) => ShowEpisodeLight.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}

class ArtworkUrls {
  final String? poster;
  final String? backdrop;

  const ArtworkUrls({this.poster, this.backdrop});

  factory ArtworkUrls.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ArtworkUrls();
    return ArtworkUrls(
      poster: json['poster'] as String?,
      backdrop: json['backdrop'] as String?,
    );
  }
}

class ShowEpisode {
  final int episodeNumber;
  final String? title;
  final String? overview;
  final String? airDate;
  final double? rating;
  final int? runtime;
  final String? still;
  final bool hasFile;
  final bool optimized;
  final String? mediaId;
  final String? localTitle;

  const ShowEpisode({
    this.episodeNumber = 0,
    this.title,
    this.overview,
    this.airDate,
    this.rating,
    this.runtime,
    this.still,
    this.hasFile = false,
    this.optimized = false,
    this.mediaId,
    this.localTitle,
  });

  factory ShowEpisode.fromJson(Map<String, dynamic> json) {
    return ShowEpisode(
      episodeNumber: (json['episode_number'] as num?)?.toInt() ?? 0,
      title: json['title'] as String?,
      overview: json['overview'] as String?,
      airDate: json['air_date'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
      runtime: (json['runtime'] as num?)?.toInt(),
      still: json['still'] as String?,
      hasFile: json['has_file'] as bool? ?? false,
      optimized: json['optimized'] as bool? ?? false,
      mediaId: json['media_id'] as String?,
      localTitle: json['local_title'] as String?,
    );
  }
}

class ShowSeason {
  final int seasonNumber;
  final String name;
  final List<ShowEpisode> episodes;

  const ShowSeason({this.seasonNumber = 1, this.name = '', this.episodes = const []});

  factory ShowSeason.fromJson(Map<String, dynamic> json) {
    return ShowSeason(
      seasonNumber: (json['season_number'] as num?)?.toInt() ?? 1,
      name: json['name'] as String? ?? '',
      episodes: (json['episodes'] as List?)
              ?.map((e) => ShowEpisode.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}

class ShowDetail {
  final String seriesTitle;
  final int? tmdbId;
  final int? year;
  final double? rating;
  final String? status;
  final String? overview;
  final List<String> genres;
  final List<String> networks;
  final List<String> creators;
  final String? firstAirDate;
  final String? lastAirDate;
  final Artwork artwork;
  final ArtworkUrls artworkUrls;
  final List<ShowSeason> seasons;

  const ShowDetail({
    this.seriesTitle = '',
    this.tmdbId,
    this.year,
    this.rating,
    this.status,
    this.overview,
    this.genres = const [],
    this.networks = const [],
    this.creators = const [],
    this.firstAirDate,
    this.lastAirDate,
    this.artwork = const Artwork(),
    this.artworkUrls = const ArtworkUrls(),
    this.seasons = const [],
  });

  factory ShowDetail.fromJson(Map<String, dynamic> json) {
    return ShowDetail(
      seriesTitle: json['series_title'] as String? ?? '',
      tmdbId: (json['tmdb_id'] as num?)?.toInt(),
      year: (json['year'] as num?)?.toInt(),
      rating: (json['rating'] as num?)?.toDouble(),
      status: json['status'] as String?,
      overview: json['overview'] as String?,
      genres: (json['genres'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      networks: (json['networks'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      creators: (json['creators'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      firstAirDate: json['first_air_date'] as String?,
      lastAirDate: json['last_air_date'] as String?,
      artwork: Artwork.fromJson(json['artwork'] as Map<String, dynamic>?),
      artworkUrls: ArtworkUrls.fromJson(json['artwork_urls'] as Map<String, dynamic>?),
      seasons: (json['seasons'] as List?)
              ?.map((e) => ShowSeason.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}
