import 'metadata.dart';

class Item {
  final String mediaId;
  final String kind;
  final String libraryId;
  final String title;
  final int? year;
  final int? season;
  final int? episode;
  final String? seriesTitle;
  final String displayTitle;
  final bool hasMetadata;
  final bool optimized;
  final Artwork artwork;

  const Item({
    required this.mediaId,
    this.kind = 'movie',
    this.libraryId = '',
    this.title = '',
    this.year,
    this.season,
    this.episode,
    this.seriesTitle,
    this.displayTitle = '',
    this.hasMetadata = false,
    this.optimized = false,
    this.artwork = const Artwork(),
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      mediaId: json['media_id'] as String? ?? '',
      kind: json['kind'] as String? ?? 'movie',
      libraryId: json['library_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      year: (json['year'] as num?)?.toInt(),
      season: (json['season'] as num?)?.toInt(),
      episode: (json['episode'] as num?)?.toInt(),
      seriesTitle: json['series_title'] as String?,
      displayTitle: json['display_title'] as String? ?? '',
      hasMetadata: json['has_metadata'] as bool? ?? false,
      optimized: json['optimized'] as bool? ?? false,
      artwork: Artwork.fromJson(json['artwork'] as Map<String, dynamic>?),
    );
  }

  bool get isEpisode => kind == 'episode';

  String get subtitleText {
    if (isEpisode && season != null && episode != null) {
      return 'S${season!.toString().padLeft(2, '0')}E${episode!.toString().padLeft(2, '0')}';
    }
    return year?.toString() ?? '';
  }
}

class ItemDetail {
  final Item item;
  final Metadata? metadata;

  const ItemDetail({required this.item, this.metadata});

  factory ItemDetail.fromJson(Map<String, dynamic> json) {
    return ItemDetail(
      item: Item.fromJson(json),
      metadata: json['metadata'] == null
          ? null
          : Metadata.fromJson(json['metadata'] as Map<String, dynamic>),
    );
  }
}
