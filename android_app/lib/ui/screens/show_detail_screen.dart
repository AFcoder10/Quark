import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/queue.dart';
import '../../models/show.dart';
import '../../models/state.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';
import '../widgets/state_views.dart';
import 'queue_screen.dart';

class ShowDetailScreen extends ConsumerStatefulWidget {
  final String seriesTitle;

  const ShowDetailScreen({super.key, required this.seriesTitle});

  @override
  ConsumerState<ShowDetailScreen> createState() => _ShowDetailScreenState();
}

class _ShowDetailScreenState extends ConsumerState<ShowDetailScreen> {
  int _season = 1;

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(showDetailProvider(widget.seriesTitle));
    final states = ref.watch(statesProvider).value ?? const <String, PlaybackState>{};
    final queueAsync = ref.watch(queueProvider).value ?? const <OptimizeJob>[];
    final queueMap = {for (final j in queueAsync) j.mediaId: j};

    return Scaffold(
      body: detailAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.accent)),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(showDetailProvider(widget.seriesTitle)),
        ),
        data: (detail) {
          final backdrop = detail.artworkUrls.backdrop;
          final poster = detail.artworkUrls.poster;
          final api = ref.watch(apiClientProvider);
          final backdropUrl = api != null && backdrop != null ? api.resolveUrl(backdrop) : null;
          final posterUrl = api != null && poster != null ? api.resolveUrl(poster) : null;

          if (detail.seasons.isNotEmpty && _season > detail.seasons.last.seasonNumber) {
            _season = detail.seasons.last.seasonNumber;
          }
          final season = detail.seasons.isNotEmpty
              ? detail.seasons.firstWhere(
                  (s) => s.seasonNumber == _season,
                  orElse: () => detail.seasons.first,
                )
              : null;

          return CustomScrollView(
            slivers: [
              SliverAppBar(
                expandedHeight: 220,
                pinned: true,
                stretch: true,
                backgroundColor: AppColors.background,
                foregroundColor: AppColors.text,
                flexibleSpace: FlexibleSpaceBar(
                  background: Stack(
                    fit: StackFit.expand,
                    children: [
                      backdropUrl == null
                          ? const _BackdropPlaceholder()
                          : CachedNetworkImage(
                              imageUrl: backdropUrl,
                              fit: BoxFit.cover,
                              errorWidget: (_, _, _) => const _BackdropPlaceholder(),
                            ),
                      const DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            stops: [0.3, 0.75, 1],
                            colors: [Colors.transparent, Color(0x660D0D12), AppColors.background],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                actions: [
                  PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert_rounded, color: AppColors.textDim),
                    onSelected: (value) {
                      final api = ref.read(apiClientProvider);
                      if (api == null) return;
                      switch (value) {
                        case 'optimize_show':
                          api.optimizeShow(widget.seriesTitle);
                          _toast('Optimization queued for all episodes');
                          ref.invalidate(queueProvider);
                        case 'optimize_season':
                          if (season != null) {
                            api.optimizeSeason(widget.seriesTitle, season.seasonNumber);
                            _toast('Optimization queued for season ${season.seasonNumber}');
                            ref.invalidate(queueProvider);
                          }
                        case 'refresh':
                          api.scanAll();
                          _toast('Scan started');
                        case 'queue':
                          _openQueue();
                      }
                    },
                    itemBuilder: (_) => [
                      const PopupMenuItem(value: 'optimize_show', child: Text('Optimize all episodes')),
                      const PopupMenuItem(value: 'optimize_season', child: Text('Optimize this season')),
                      const PopupMenuItem(value: 'refresh', child: Text('Scan libraries')),
                      const PopupMenuItem(value: 'queue', child: Text('Optimization queue')),
                    ],
                  ),
                ],
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: SizedBox(
                          width: 88,
                          height: 132,
                          child: posterUrl == null
                              ? const _SmallPosterPlaceholder()
                              : CachedNetworkImage(
                                  imageUrl: posterUrl,
                                  fit: BoxFit.cover,
                                  errorWidget: (_, _, _) => const _SmallPosterPlaceholder(),
                                ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              detail.seriesTitle,
                              style: const TextStyle(
                                color: AppColors.text,
                                fontSize: 19,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.3,
                              ),
                            ),
                            const SizedBox(height: 6),
                            _metaRow(detail),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: [
                                for (final g in detail.genres.take(4))
                                  _Tag(text: g),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if ((detail.overview ?? '').isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                    child: Text(
                      detail.overview!,
                      maxLines: 4,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: AppColors.textDim, fontSize: 13.5, height: 1.5),
                    ),
                  ),
                ),
              if (detail.seasons.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          for (final s in detail.seasons)
                            Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ChoiceChip(
                                label: Text(s.seasonNumber == 0 ? 'Specials' : 'Season ${s.seasonNumber}'),
                                selected: _season == s.seasonNumber,
                                onSelected: (_) => setState(() => _season = s.seasonNumber),
                                labelStyle: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w600,
                                  color: _season == s.seasonNumber
                                      ? AppColors.accentBright
                                      : AppColors.textDim,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              if (season != null)
                SliverList.builder(
                  itemCount: season.episodes.length,
                  itemBuilder: (context, i) {
                    final ep = season.episodes[i];
                    final st = ep.mediaId != null ? states[ep.mediaId] : null;
                    final job = ep.mediaId != null ? queueMap[ep.mediaId] : null;
                    return _EpisodeTile(
                      episode: ep,
                      state: st,
                      job: job,
                      onPlay: () {
                        if (ep.mediaId == null) return;
                        playItem(
                          context,
                          mediaId: ep.mediaId!,
                          title: ep.title ?? '${widget.seriesTitle} S${season.seasonNumber}E${ep.episodeNumber}',
                          initialPosition: st?.isResumable == true ? st!.position : 0,
                        );
                      },
                      onQueueOpen: _openQueue,
                    );
                  },
                ),
              const SliverToBoxAdapter(child: SizedBox(height: 32)),
            ],
          );
        },
      ),
    );
  }

  Widget _metaRow(ShowDetail detail) {
    final parts = <String>[
      if (detail.year != null) '${detail.year}',
      if (detail.rating != null) '★ ${detail.rating!.toStringAsFixed(1)}',
      if (detail.seasons.isNotEmpty) '${detail.seasons.length} season${detail.seasons.length == 1 ? '' : 's'}',
      if (detail.status != null && detail.status!.isNotEmpty) detail.status!,
    ];
    return Text(
      parts.join('  ·  '),
      style: const TextStyle(color: AppColors.textFaint, fontSize: 12),
    );
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..clearSnackBars()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  void _openQueue() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const QueueScreen()),
    );
  }
}

class _Tag extends StatelessWidget {
  final String text;
  const _Tag({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.elevated,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: const TextStyle(color: AppColors.textDim, fontSize: 11),
      ),
    );
  }
}

class _EpisodeTile extends StatelessWidget {
  final ShowEpisode episode;
  final PlaybackState? state;
  final OptimizeJob? job;
  final VoidCallback onPlay;
  final VoidCallback onQueueOpen;

  const _EpisodeTile({
    required this.episode,
    required this.state,
    required this.job,
    required this.onPlay,
    required this.onQueueOpen,
  });

  @override
  Widget build(BuildContext context) {
    final watched = state?.watched ?? false;
    final resumable = state?.isResumable ?? false;

    return InkWell(
      onTap: onPlay,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
        child: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: AppColors.elevated,
                borderRadius: BorderRadius.circular(9),
              ),
              child: Center(
                child: Text(
                  '${episode.episodeNumber}',
                  style: const TextStyle(
                    color: AppColors.textDim,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          episode.title ?? 'Episode ${episode.episodeNumber}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: AppColors.text,
                            fontSize: 13.5,
                            fontWeight: FontWeight.w600,
                            decoration: watched ? TextDecoration.lineThrough : null,
                            decorationColor: AppColors.textFaint,
                          ),
                        ),
                      ),
                      if (episode.optimized) ...[
                        const SizedBox(width: 6),
                        const Icon(Icons.done_all, color: AppColors.accentBright, size: 14),
                      ],
                      if (job != null && job!.isActive) ...[
                        const SizedBox(width: 6),
                        const Icon(Icons.autorenew, color: AppColors.warning, size: 14),
                      ],
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _subtitle(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: AppColors.textFaint, fontSize: 11),
                  ),
                ],
              ),
            ),
            if (resumable) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.accent.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _format(state!.position),
                  style: const TextStyle(color: AppColors.accentBright, fontSize: 10.5, fontWeight: FontWeight.w700),
                ),
              ),
            ],
            const SizedBox(width: 4),
            const Icon(Icons.play_arrow_rounded, color: AppColors.textFaint, size: 24),
          ],
        ),
      ),
    );
  }

  String _subtitle() {
    final parts = <String>[];
    if (episode.airDate != null && episode.airDate!.isNotEmpty) parts.add(episode.airDate!);
    if (episode.runtime != null && episode.runtime! > 0) parts.add('${episode.runtime} min');
    return parts.join('  ·  ');
  }

  String _format(double seconds) {
    final m = (seconds / 60).floor();
    final s = (seconds % 60).floor();
    return '$m:${s.toString().padLeft(2, '0')}';
  }
}

class _BackdropPlaceholder extends StatelessWidget {
  const _BackdropPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      child: const Center(
        child: Icon(Icons.live_tv_outlined, color: AppColors.textFaint, size: 40),
      ),
    );
  }
}

class _SmallPosterPlaceholder extends StatelessWidget {
  const _SmallPosterPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.elevated,
      child: const Center(
        child: Icon(Icons.live_tv_outlined, color: AppColors.textFaint, size: 26),
      ),
    );
  }
}
