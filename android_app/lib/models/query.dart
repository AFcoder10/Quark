import 'item.dart';

class ItemQuery {
  final String? libraryId;
  final String? kind;
  final String? search;
  final List<String> genres;
  final bool? unwatched;
  final String? sort;
  final int? limit;
  final int offset;

  const ItemQuery({
    this.libraryId,
    this.kind,
    this.search,
    this.genres = const [],
    this.unwatched,
    this.sort,
    this.limit,
    this.offset = 0,
  });

  Map<String, dynamic> toJson() {
    return {
      if (libraryId != null) 'library_id': libraryId,
      if (kind != null) 'kind': kind,
      if (search != null && search!.isNotEmpty) 'search': search,
      if (genres.isNotEmpty) 'genres': genres,
      if (unwatched != null) 'unwatched': unwatched,
      if (sort != null) 'sort': sort,
      if (limit != null) 'limit': limit,
      'offset': offset,
    };
  }
}

class QueryResult {
  final List<Item> items;
  final int total;

  const QueryResult({this.items = const [], this.total = 0});

  factory QueryResult.fromJson(Map<String, dynamic> json) {
    return QueryResult(
      items: (json['items'] as List?)
              ?.map((e) => Item.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      total: (json['total'] as num?)?.toInt() ?? 0,
    );
  }
}
