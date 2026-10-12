import 'package:dio/dio.dart';

import '../models/health.dart';
import '../models/item.dart';
import '../models/library.dart';
import '../models/metadata.dart';
import '../models/queue.dart';
import '../models/query.dart';
import '../models/show.dart';
import '../models/state.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  const ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiClient {
  final String baseUrl;
  final Dio _dio;

  ApiClient({required String baseUrl})
      : baseUrl = baseUrl,
        _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl,
            connectTimeout: const Duration(seconds: 8),
            receiveTimeout: const Duration(seconds: 30),
            sendTimeout: const Duration(seconds: 15),
            headers: {'Accept': 'application/json'},
          ),
        );

  T _handle<T>(T Function(dynamic data) parse, Response response) {    if (response.statusCode == 204) throw const ApiException('Empty response');
    return parse(response.data);
  }

  Future<T> _get<T>(String path, T Function(dynamic) parse) async {
    try {
      final res = await _dio.get(path);
      return _handle(parse, res);
    } on DioException catch (e) {
      throw _toApi(e);
    }
  }

  Future<T> _post<T>(String path, T Function(dynamic) parse, {Object? body}) async {
    try {
      final res = await _dio.post(path, data: body);
      return _handle(parse, res);
    } on DioException catch (e) {
      throw _toApi(e);
    }
  }

  Future<void> _delete(String path) async {
    try {
      await _dio.delete(path);
    } on DioException catch (e) {
      throw _toApi(e);
    }
  }

  Future<T> _query<T>(String path, Map<String, dynamic> body, T Function(dynamic) parse) async {
    try {
      final res = await _dio.request(
        path,
        data: body,
        options: Options(
          method: 'QUERY',
          contentType: Headers.jsonContentType,
          headers: {'Accept': 'application/json'},
        ),
      );
      return _handle(parse, res);
    } on DioException catch (e) {
      throw _toApi(e);
    }
  }

  ApiException _toApi(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.connectionError) {
      return const ApiException('Cannot reach server. Check the address and try again.');
    }
    if (e.type == DioExceptionType.receiveTimeout) {
      return const ApiException('Server took too long to respond.');
    }
    final status = e.response?.statusCode;
    String detail = e.response?.data is Map<String, dynamic>
        ? (e.response!.data['detail']?.toString() ?? e.message ?? '')
        : (e.response?.data?.toString() ?? e.message ?? '');
    if (detail == '') detail = e.message ?? 'Request failed';
    return ApiException(detail, statusCode: status);
  }

  // ── System ──────────────────────────────────────────────────────────────
  Future<Health> health() async => _get('/api/system/health', (d) => Health.fromJson(d as Map<String, dynamic>));

  Future<bool> testConnection() async {
    try {
      final h = await health();
      return h.isOk;
    } catch (_) {
      return false;
    }
  }

  // ── Libraries ───────────────────────────────────────────────────────────
  Future<List<Library>> libraries() async =>
      _get('/api/libraries', (d) => (d as List).map((e) => Library.fromJson(e as Map<String, dynamic>)).toList());

  Future<void> scanLibrary(String libraryId) async => _post('/api/libraries/$libraryId/scan', (_) {});

  Future<void> scanAll() async => _post('/api/libraries/scan-all', (_) {});

  // ── Items ───────────────────────────────────────────────────────────────
  Future<List<Item>> items({String? kind, String? libraryId, String? search}) async {
    final params = <String, String>{
      'kind': ?kind,
      'library_id': ?libraryId,
      'search': ?search,
    };
    final qs = params.entries.map((e) => '${e.key}=${Uri.encodeQueryComponent(e.value)}').join('&');
    final path = qs.isEmpty ? '/api/items' : '/api/items?$qs';
    return _get(path, (d) => (d as List).map((e) => Item.fromJson(e as Map<String, dynamic>)).toList());
  }

  Future<QueryResult> queryItems(ItemQuery query) async =>
      _query('/api/items', query.toJson(), (d) => QueryResult.fromJson(d as Map<String, dynamic>));

  Future<List<String>> genres() async =>
      _get('/api/items/genres', (d) => (d as List).map((e) => e.toString()).toList());

  Future<ItemDetail> itemDetail(String mediaId) async =>
      _get('/api/items/$mediaId?client=android', (d) => ItemDetail.fromJson(d as Map<String, dynamic>));

  Future<List<SubtitleTrack>> subtitleTracks(String mediaId) async =>
      _get('/api/items/$mediaId/subtitles', (d) => (d as List).map((e) => SubtitleTrack.fromJson(e as Map<String, dynamic>)).toList());

  Future<String> subtitleFile(String mediaId, int index) async {
    final res = await _dio.get('/api/items/$mediaId/subtitles/$index');
    return res.data?.toString() ?? '';
  }

  Future<void> refreshItem(String mediaId) async => _post('/api/items/$mediaId/refresh', (_) {});

  Future<void> deleteItem(String mediaId) async => _delete('/api/items/$mediaId');

  // ── Shows ───────────────────────────────────────────────────────────────
  Future<List<Show>> shows() async =>
      _get('/api/shows', (d) => (d as List).map((e) => Show.fromJson(e as Map<String, dynamic>)).toList());

  Future<ShowDetail> showDetail(String seriesTitle) async {
    final encoded = Uri.encodeComponent(seriesTitle);
    return _get('/api/shows/$encoded', (d) => ShowDetail.fromJson(d as Map<String, dynamic>));
  }

  Future<void> optimizeShow(String seriesTitle, {String mode = 'hls'}) async {
    final encoded = Uri.encodeComponent(seriesTitle);
    await _post('/api/shows/$encoded/optimize?mode=$mode', (_) {});
  }

  Future<void> optimizeSeason(String seriesTitle, int season, {String mode = 'hls'}) async {
    final encoded = Uri.encodeComponent(seriesTitle);
    await _post('/api/shows/$encoded/seasons/$season/optimize?mode=$mode', (_) {});
  }

  // ── State ───────────────────────────────────────────────────────────────
  Future<PlaybackState> state(String mediaId) async =>
      _get('/api/state/$mediaId', (d) => PlaybackState.fromJson(d as Map<String, dynamic>));

  Future<Map<String, PlaybackState>> allStates() async {
    final res = await _get('/api/state/watched', (d) => d as Map<String, dynamic>);
    final items = (res['items'] as Map<String, dynamic>? ?? {});
    return items.map((k, v) => MapEntry(k, PlaybackState.fromJson(v as Map<String, dynamic>?)));
  }

  Future<List<RecentState>> recent() async =>
      _get('/api/state/recent', (d) => (d as List).map((e) => RecentState.fromJson(e as Map<String, dynamic>)).toList());

  Future<void> saveProgress(String mediaId, double position, double duration) async {
    await _post('/api/state/$mediaId/progress', (_) {}, body: {'position': position, 'duration': duration});
  }

  Future<void> markWatched(String mediaId, {bool watched = true}) async {
    await _post('/api/state/$mediaId/watch', (_) {}, body: {'watched': watched});
  }

  // ── Optimization ────────────────────────────────────────────────────────
  Future<List<OptimizeJob>> optimizeQueue() async =>
      _get('/api/optimize/queue', (d) => (d['jobs'] as List? ?? []).map((e) => OptimizeJob.fromJson(e as Map<String, dynamic>)).toList());

  Future<OptimizeJob?> optimizeStatus(String mediaId) async =>
      _get('/api/items/$mediaId/optimize/status', (d) => OptimizeJob.fromJson(d as Map<String, dynamic>));

  Future<void> optimize(String mediaId, {String mode = 'hls'}) async {
    await _post('/api/items/$mediaId/optimize?mode=$mode', (_) {});
  }

  Future<void> cancelOptimize(String mediaId) async => _delete('/api/items/$mediaId/optimize');

  // ── Stream URLs ─────────────────────────────────────────────────────────
  String hlsUrl(String mediaId) => '$baseUrl/api/items/$mediaId/hls/master.m3u8';

  String directUrl(String mediaId) => '$baseUrl/api/items/$mediaId/stream?mode=direct&client=android';

  String transcodeUrl(String mediaId, {int height = 1080, double start = 0}) =>
      '$baseUrl/api/items/$mediaId/stream?mode=transcode&height=$height&start=$start';

  String artworkUrl(String mediaId, String name) => '$baseUrl/api/items/$mediaId/artwork/$name';

  String resolveUrl(String path) =>
      path.startsWith('http') ? path : '$baseUrl${path.startsWith('/') ? path : '/$path'}';
}
