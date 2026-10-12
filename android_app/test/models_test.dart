import 'package:flutter_test/flutter_test.dart';
import 'package:quark_android/core/app_config.dart';
import 'package:quark_android/models/item.dart';
import 'package:quark_android/models/query.dart';
import 'package:quark_android/models/show.dart';
import 'package:quark_android/models/state.dart';

void main() {
  group('normalizeServerUrl', () {
    test('adds http:// when missing', () {
      expect(normalizeServerUrl('192.168.1.50:16967'), 'http://192.168.1.50:16967');
    });

    test('keeps https scheme', () {
      expect(normalizeServerUrl('https://myserver:16967'), 'https://myserver:16967');
    });

    test('trims trailing slashes', () {
      expect(normalizeServerUrl('http://192.168.1.50:16967/'), 'http://192.168.1.50:16967');
    });

    test('trims whitespace', () {
      expect(normalizeServerUrl('  192.168.1.50:16967  '), 'http://192.168.1.50:16967');
    });
  });

  group('Item.fromJson', () {
    test('parses movie summary', () {
      final item = Item.fromJson({
        'media_id': 'mv-abc123',
        'kind': 'movie',
        'title': 'Backrooms',
        'year': 2022,
        'display_title': 'Backrooms',
        'optimized': true,
        'artwork': {'poster': '/api/items/mv-abc123/artwork/poster'},
      });

      expect(item.mediaId, 'mv-abc123');
      expect(item.kind, 'movie');
      expect(item.title, 'Backrooms');
      expect(item.year, 2022);
      expect(item.optimized, true);
      expect(item.artwork.poster, '/api/items/mv-abc123/artwork/poster');
      expect(item.isEpisode, false);
      expect(item.subtitleText, '2022');
    });

    test('parses episode display title', () {
      final item = Item.fromJson({
        'media_id': 'ep-1',
        'kind': 'episode',
        'season': 2,
        'episode': 5,
        'series_title': 'Test Show',
        'display_title': 'Test Show S02E05',
      });

      expect(item.isEpisode, true);
      expect(item.subtitleText, 'S02E05');
    });
  });

  group('ItemQuery.toJson', () {
    test('omits null fields', () {
      const query = ItemQuery();
      expect(query.toJson(), {'offset': 0});
    });

    test('includes provided filters', () {
      const query = ItemQuery(
        search: 'back',
        genres: ['Horror'],
        unwatched: true,
        sort: 'rating',
        limit: 50,
      );
      final json = query.toJson();
      expect(json['search'], 'back');
      expect(json['genres'], ['Horror']);
      expect(json['unwatched'], true);
      expect(json['sort'], 'rating');
      expect(json['limit'], 50);
    });
  });

  group('PlaybackState', () {
    test('isResumable logic', () {
      final resumable = PlaybackState(position: 120, duration: 600, watched: false);
      expect(resumable.isResumable, true);

      final watched = PlaybackState(position: 500, duration: 600, watched: true);
      expect(watched.isResumable, false);

      final nearEnd = PlaybackState(position: 590, duration: 600, watched: false);
      expect(nearEnd.isResumable, false);
    });

    test('progress percent', () {
      final state = PlaybackState(position: 300, duration: 600);
      expect(state.progressPct, 50.0);
    });
  });

  group('Show.fromJson', () {
    test('parses show summary', () {
      final show = Show.fromJson({
        'series_title': 'Breaking Bad',
        'year': 2008,
        'rating': 9.5,
        'episode_count': 62,
        'artwork_urls': {'poster': '/api/items/ep-1/artwork/poster'},
      });

      expect(show.seriesTitle, 'Breaking Bad');
      expect(show.year, 2008);
      expect(show.rating, 9.5);
      expect(show.episodeCount, 62);
      expect(show.artworkUrls.poster, '/api/items/ep-1/artwork/poster');
    });
  });
}
