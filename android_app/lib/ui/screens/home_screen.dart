import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/item.dart';
import '../../models/state.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';
import '../widgets/continue_watching_card.dart';
import '../widgets/poster_card.dart';
import '../widgets/section_header.dart';
import '../widgets/shimmer.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final recentAsync = ref.watch(recentProvider);
    final itemsAsync = ref.watch(itemsProvider);
    final recentAsync2 = ref.watch(recentlyAddedProvider);
    final states = ref.watch(statesProvider).value ?? const <String, PlaybackState>{};

    final continueWatching = _buildContinueWatching(recentAsync, itemsAsync);
    final recentlyAdded = recentAsync2.value ?? const <Item>[];
    final featured = _featured(recentlyAdded);

    final loading = recentAsync.isLoading && itemsAsync.isLoading && recentAsync2.isLoading;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Quark', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
            if (settings.serverName != null && settings.serverName!.isNotEmpty)
              Text(
                settings.serverName!,
                style: const TextStyle(fontSize: 11, color: AppColors.textFaint, fontWeight: FontWeight.w500),
              ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Scan libraries',
            onPressed: () {
              final api = ref.read(apiClientProvider);
              if (api == null) return;
              api.scanAll();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Scan started')),
              );
            },
            icon: const Icon(Icons.sync, size: 22, color: AppColors.textDim),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(recentProvider);
          ref.invalidate(itemsProvider);
          ref.invalidate(recentlyAddedProvider);
          await Future.wait([
            ref.read(recentProvider.future).catchError((_) => const <Never>[]),
            ref.read(itemsProvider.future).catchError((_) => const <Never>[]),
          ]);
        },
        color: AppColors.accent,
        child: loading
            ? ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.only(top: 4, bottom: 24),
                children: const [
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: BannerSkeleton(height: 210),
                  ),
                  SizedBox(height: 20),
                  RowSkeleton(),
                  SizedBox(height: 24),
                  PosterGridSkeleton(),
                ],
              )
            : ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.only(bottom: 24),
                children: [
                  if (featured != null) ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: _HomeBanner(
                        item: featured,
                        resumePosition: states[featured.mediaId]?.isResumable == true
                            ? states[featured.mediaId]!.position
                            : 0,
                      ),
                    ),
                    const SizedBox(height: 18),
                  ],
                  if (continueWatching != null) ...[
                    const Padding(
                      padding: EdgeInsets.only(left: 16, right: 16),
                      child: SectionHeader(title: 'Continue Watching'),
                    ),
                    SizedBox(height: 158, child: continueWatching),
                  ],
                  if (recentlyAdded.isNotEmpty) ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: SectionHeader(
                        title: 'Recently Added',
                        trailing: 'See All',
                        onTrailingTap: () =>
                            ref.read(tabIndexProvider.notifier).state = 1,
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 3,
                          crossAxisSpacing: 10,
                          mainAxisSpacing: 12,
                          childAspectRatio: 0.52,
                        ),
                        itemCount: recentlyAdded.length,
                        itemBuilder: (context, i) {
                          final item = recentlyAdded[i];
                          return PosterCard(
                            item: item,
                            heroTag: 'poster-${item.mediaId}',
                            onTap: () => openItem(context, item),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
      ),
    );
  }

  Item? _featured(List<Item> items) {
    if (items.isEmpty) return null;
    return items.firstWhere(
      (i) => i.artwork.backdrop != null,
      orElse: () => items.first,
    );
  }

  Widget? _buildContinueWatching(
    AsyncValue<List<RecentState>> recentAsync,
    AsyncValue<List<Item>> itemsAsync,
  ) {
    if (recentAsync.isLoading || itemsAsync.isLoading) return null;
    final recent = recentAsync.value ?? const <RecentState>[];
    final items = itemsAsync.value ?? const <Item>[];
    if (recent.isEmpty) return null;
    final itemMap = {for (final i in items) i.mediaId: i};
    final entries = recent
        .map((r) => (itemMap[r.mediaId], r))
        .where((e) => e.$1 != null)
        .toList();
    if (entries.isEmpty) return null;

    return ListView.separated(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: entries.length,
      separatorBuilder: (_, _) => const SizedBox(width: 12),
      itemBuilder: (context, i) {
        final item = entries[i].$1!;
        final state = entries[i].$2;
        return ContinueWatchingCard(
          item: item,
          state: state,
          onPlay: () => playItem(
            context,
            mediaId: item.mediaId,
            title: item.displayTitle,
            initialPosition: state.position,
          ),
        );
      },
    );
  }
}

class _HomeBanner extends ConsumerWidget {
  final Item item;
  final double resumePosition;

  const _HomeBanner({required this.item, required this.resumePosition});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(apiClientProvider);
    final hasBackdrop = item.artwork.backdrop != null;
    final url = api != null && (hasBackdrop || item.artwork.poster != null)
        ? api.artworkUrl(item.mediaId, hasBackdrop ? 'backdrop' : 'poster')
        : null;

    final resume = resumePosition > 0;

    return Container(
      height: 216,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.4),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Stack(
          fit: StackFit.expand,
          children: [
            url == null
                ? const _BannerPlaceholder()
                : CachedNetworkImage(
                    imageUrl: url,
                    fit: BoxFit.cover,
                    fadeInDuration: const Duration(milliseconds: 250),
                    placeholder: (_, _) => const ShimmerBox(borderRadius: BorderRadius.all(Radius.circular(18))),
                    errorWidget: (_, _, _) => const _BannerPlaceholder(),
                  ),
            DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withValues(alpha: 0.15),
                    Colors.black.withValues(alpha: 0.35),
                    Colors.black.withValues(alpha: 0.82),
                  ],
                  stops: const [0, 0.55, 1],
                ),
              ),
            ),
            Positioned(
              left: 18,
              right: 18,
              bottom: 16,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.subtitleText.isEmpty ? item.displayTitle : item.subtitleText,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.4,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    item.displayTitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 23,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.4,
                      height: 1.1,
                      shadows: [Shadow(blurRadius: 8, color: Colors.black)],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      FilledButton.icon(
                        onPressed: () => playItem(
                          context,
                          mediaId: item.mediaId,
                          title: item.displayTitle,
                          initialPosition: resumePosition,
                        ),
                        style: FilledButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.black,
                          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                        ),
                        icon: Icon(resume ? Icons.play_circle_fill_rounded : Icons.play_arrow_rounded, size: 20),
                        label: Text(resume ? 'Resume' : 'Play'),
                      ),
                      const SizedBox(width: 10),
                      OutlinedButton.icon(
                        onPressed: () => openItem(context, item),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: Colors.white,
                          side: const BorderSide(color: Colors.white54),
                          backgroundColor: Colors.black.withValues(alpha: 0.25),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        icon: const Icon(Icons.info_outline_rounded, size: 18),
                        label: const Text('Details'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BannerPlaceholder extends StatelessWidget {
  const _BannerPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.elevated, AppColors.surface],
        ),
      ),
      child: const Center(child: Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 44)),
    );
  }
}
