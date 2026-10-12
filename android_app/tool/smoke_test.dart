import 'dart:io';

import 'package:quark_android/core/api_client.dart';
import 'package:quark_android/models/query.dart';

Future<void> main(List<String> args) async {
  final baseUrl = args.isNotEmpty ? args.first : 'http://127.0.0.1:16967';
  stdout.writeln('SMOKE TEST against $baseUrl\n');
  final api = ApiClient(baseUrl: baseUrl);
  var failures = 0;

  Future<void> check(String name, Future<bool> Function() run) async {
    try {
      final ok = await run();
      if (ok) {
        stdout.writeln('  PASS  $name');
      } else {
        failures++;
        stdout.writeln('  FAIL  $name');
      }
    } catch (e) {
      failures++;
      stdout.writeln('  FAIL  $name -> $e');
    }
  }

  await check('health', () async => (await api.health()).isOk);

  await check('libraries', () async {
    final libs = await api.libraries();
    stdout.writeln('        libraries: ${libs.map((l) => l.name).toList()}');
    return libs.isNotEmpty;
  });

  await check('items (GET)', () async {
    final items = await api.items();
    stdout.writeln('        items: ${items.length}, first: ${items.isNotEmpty ? items.first.displayTitle : 'n/a'}');
    return items.isNotEmpty;
  });

  await check('queryItems (QUERY method)', () async {
    final qr = await api.queryItems(const ItemQuery(search: 'back', sort: 'title', limit: 5));
    stdout.writeln('        QUERY "back": total=${qr.total}, items=${qr.items.map((i) => i.displayTitle).toList()}');
    return qr.total > 0;
  });

  await check('queryItems genre filter', () async {
    final qr = await api.queryItems(const ItemQuery(genres: ['Horror']));
    stdout.writeln('        Horror: total=${qr.total}');
    return true;
  });

  await check('genres', () async {
    final genres = await api.genres();
    stdout.writeln('        genres: $genres');
    return genres.isNotEmpty;
  });

  await check('shows', () async {
    final shows = await api.shows();
    stdout.writeln('        shows: ${shows.length}, first: ${shows.isNotEmpty ? shows.first.seriesTitle : 'n/a'}');
    return true;
  });

  await check('state/recent', () async {
    final recent = await api.recent();
    stdout.writeln('        recent: ${recent.length}');
    return true;
  });

  await check('allStates', () async {
    final states = await api.allStates();
    stdout.writeln('        states: ${states.length}');
    return true;
  });

  await check('optimizeQueue', () async {
    final jobs = await api.optimizeQueue();
    stdout.writeln('        jobs: ${jobs.length}');
    return true;
  });

  stdout.writeln('\n${failures == 0 ? "ALL SMOKE CHECKS PASSED" : "$failures CHECKS FAILED"}');
  exit(failures == 0 ? 0 : 1);
}
