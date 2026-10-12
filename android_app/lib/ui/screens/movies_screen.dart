import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/state.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';
import '../widgets/empty_state.dart';
import '../widgets/poster_card.dart';
import '../widgets/shimmer.dart';
import '../widgets/state_views.dart';

class MoviesScreen extends ConsumerStatefulWidget {
  const MoviesScreen({super.key});

  @override
  ConsumerState<MoviesScreen> createState() => _MoviesScreenState();
}

class _MoviesScreenState extends ConsumerState<MoviesScreen> {
  String _sort = 'title';
  bool _unwatched = false;

  @override
  Widget build(BuildContext context) {
    final filter = MovieFilter(sort: _sort, unwatched: _unwatched);
    final movies = ref.watch(moviesProvider(filter));
    final states = ref.watch(statesProvider).value ?? const <String, PlaybackState>{};

    return Scaffold(
      appBar: AppBar(
        title: const Text('Movies'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort_rounded, color: AppColors.textDim, size: 22),
            onSelected: (value) => setState(() => _sort = value),
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'title', child: Text('Title A–Z')),
              PopupMenuItem(value: 'year', child: Text('Newest first')),
              PopupMenuItem(value: 'rating', child: Text('Highest rated')),
              PopupMenuItem(value: 'recently_added', child: Text('Recently added')),
            ],
          ),
          IconButton(
            tooltip: 'Unwatched only',
            onPressed: () => setState(() => _unwatched = !_unwatched),
            icon: Icon(
              _unwatched ? Icons.done_all_rounded : Icons.done_all_outlined,
              color: _unwatched ? AppColors.accentBright : AppColors.textFaint,
              size: 22,
            ),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: movies.when(
        loading: () => const PosterGridSkeleton(),
        error: (e, _) => ErrorView(message: e.toString(), onRetry: () => ref.invalidate(moviesProvider(filter))),
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              icon: Icons.movie_outlined,
              title: 'No movies yet',
              subtitle: 'Add a movie library in Quark and scan it.',
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(moviesProvider(filter));
              ref.invalidate(statesProvider);
              await ref.read(moviesProvider(filter).future).catchError((_) => const <Never>[]);
            },
            color: AppColors.accent,
            child: GridView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              physics: const AlwaysScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                crossAxisSpacing: 10,
                mainAxisSpacing: 12,
                childAspectRatio: 0.52,
              ),
              itemCount: items.length,
              itemBuilder: (context, i) {
                final item = items[i];
                final st = states[item.mediaId];
                return PosterCard(
                  item: item,
                  progress: st?.progressPct,
                  watched: st?.watched ?? false,
                  heroTag: 'poster-${item.mediaId}',
                  onTap: () => openItem(context, item),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
