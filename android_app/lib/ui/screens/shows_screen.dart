import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/providers.dart';
import '../../theme.dart';
import '../widgets/empty_state.dart';
import '../widgets/show_card.dart';
import '../widgets/shimmer.dart';
import '../widgets/state_views.dart';
import 'show_detail_screen.dart';

class ShowsScreen extends ConsumerWidget {
  const ShowsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shows = ref.watch(showsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Shows'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () {
              ref.invalidate(showsProvider);
              ref.invalidate(itemsProvider);
            },
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textDim, size: 22),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: shows.when(
        loading: () => const PosterGridSkeleton(),
        error: (e, _) => ErrorView(message: e.toString(), onRetry: () => ref.invalidate(showsProvider)),
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              icon: Icons.live_tv_outlined,
              title: 'No shows yet',
              subtitle: 'Add a TV library in Quark and scan it.',
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(showsProvider);
              await ref.read(showsProvider.future).catchError((_) => const <Never>[]);
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
                final show = items[i];
                return ShowCard(
                  show: show,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ShowDetailScreen(seriesTitle: show.seriesTitle),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
