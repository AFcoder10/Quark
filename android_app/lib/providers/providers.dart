import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/app_config.dart';
import '../core/ws_client.dart';
import '../models/health.dart';
import '../models/item.dart';
import '../models/library.dart';
import '../models/query.dart';
import '../models/queue.dart';
import '../models/show.dart';
import '../models/state.dart';

// ── Settings ─────────────────────────────────────────────────────────────
class SettingsNotifier extends StateNotifier<AppSettings> {
  SettingsNotifier() : super(AppSettings()) {
    _load();
  }

  Future<void> _load() async {
    final s = AppSettings();
    await s.load();
    state = s;
  }

  Future<void> setServer(String url, {String? name}) async {
    await state.setServer(url, name: name);
    await _load();
  }

  Future<void> setAllow4k(bool value) async {
    await state.setAllow4k(value);
    await _load();
  }

  Future<void> setCellularEnabled(bool value) async {
    await state.setCellularEnabled(value);
    await _load();
  }

  Future<void> setAutoResume(bool value) async {
    await state.setAutoResume(value);
    await _load();
  }

  Future<void> clearServer() async {
    await state.clear();
    await _load();
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, AppSettings>(
  (ref) => SettingsNotifier(),
);

final tabIndexProvider = StateProvider<int>((ref) => 0);

class NowPlayingInfo {
  final String mediaId;
  final String title;
  final bool playing;
  final double position;
  final double duration;

  const NowPlayingInfo({
    required this.mediaId,
    required this.title,
    this.playing = false,
    this.position = 0,
    this.duration = 0,
  });

  double get progressPct =>
      duration > 0 ? (position / duration * 100).clamp(0.0, 100.0) : 0;

  NowPlayingInfo copyWith({
    bool? playing,
    double? position,
    double? duration,
  }) {
    return NowPlayingInfo(
      mediaId: mediaId,
      title: title,
      playing: playing ?? this.playing,
      position: position ?? this.position,
      duration: duration ?? this.duration,
    );
  }
}

class NowPlayingNotifier extends StateNotifier<NowPlayingInfo?> {
  NowPlayingNotifier() : super(null);

  void setSession(String mediaId, String title) {
    state = NowPlayingInfo(mediaId: mediaId, title: title, playing: true);
  }

  void update({bool? playing, double? position, double? duration}) {
    if (state == null) return;
    state = state!.copyWith(
      playing: playing,
      position: position,
      duration: duration,
    );
  }

  void stop() {
    if (state == null) return;
    state = state!.copyWith(playing: false);
  }

  void dismiss() => state = null;
}

final nowPlayingProvider = StateNotifierProvider<NowPlayingNotifier, NowPlayingInfo?>(
  (ref) => NowPlayingNotifier(),
);

final apiClientProvider = Provider<ApiClient?>((ref) {
  final serverUrl = ref.watch(settingsProvider).serverUrl;
  if (serverUrl == null || serverUrl.isEmpty) return null;
  return ApiClient(baseUrl: serverUrl);
});

final wsClientProvider = Provider<WsClient?>((ref) {
  final serverUrl = ref.watch(settingsProvider).serverUrl;
  if (serverUrl == null || serverUrl.isEmpty) return null;
  final ws = WsClient(serverUrl);
  ref.onDispose(ws.close);
  ws.connect();
  return ws;
});

final wsEventsProvider = StreamProvider<WsEvent>((ref) {
  final ws = ref.watch(wsClientProvider);
  if (ws == null) return const Stream.empty();
  return ws.events;
});

// ── Data providers ───────────────────────────────────────────────────────
final healthProvider = FutureProvider<Health>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.health();
});

final itemsProvider = FutureProvider<List<Item>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.items();
});

final showsProvider = FutureProvider<List<Show>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.shows();
});

final showDetailProvider = FutureProvider.family<ShowDetail, String>((ref, seriesTitle) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.showDetail(seriesTitle);
});

final itemDetailProvider = FutureProvider.family<ItemDetail, String>((ref, mediaId) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.itemDetail(mediaId);
});

final recentProvider = FutureProvider<List<RecentState>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.recent();
});

final statesProvider = FutureProvider<Map<String, PlaybackState>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.allStates();
});

final genresProvider = FutureProvider<List<String>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.genres();
});

final queueProvider = FutureProvider<List<OptimizeJob>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.optimizeQueue();
});

final librariesProvider = FutureProvider<List<Library>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.libraries();
});

final recentlyAddedProvider = FutureProvider<List<Item>>((ref) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.queryItems(const ItemQuery(sort: 'recently_added', limit: 12)).then((r) => r.items);
});

class MovieFilter {
  final String sort;
  final bool unwatched;

  const MovieFilter({this.sort = 'title', this.unwatched = false});

  ItemQuery toQuery() =>
      ItemQuery(kind: 'movie', sort: sort, unwatched: unwatched ? true : null, limit: 300);

  @override
  bool operator ==(Object other) =>
      other is MovieFilter && other.sort == sort && other.unwatched == unwatched;

  @override
  int get hashCode => Object.hash(sort, unwatched);
}

final moviesProvider = FutureProvider.autoDispose.family<List<Item>, MovieFilter>((ref, filter) {
  final api = ref.watch(apiClientProvider);
  if (api == null) throw const ApiException('No server configured');
  return api.queryItems(filter.toQuery()).then((r) => r.items);
});
