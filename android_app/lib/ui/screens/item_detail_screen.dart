import 'dart:ui' show ImageFilter;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../models/metadata.dart';
import '../../models/state.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';
import '../widgets/state_views.dart';
import 'queue_screen.dart';

class ItemDetailScreen extends ConsumerStatefulWidget {
  final String mediaId;

  const ItemDetailScreen({super.key, required this.mediaId});

  @override
  ConsumerState<ItemDetailScreen> createState() => _ItemDetailScreenState();
}

class _ItemDetailScreenState extends ConsumerState<ItemDetailScreen> {
  bool _busy = false;

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(itemDetailProvider(widget.mediaId));
    final stateAsync = ref.watch(statesProvider).value ?? const <String, PlaybackState>{};

    return Scaffold(
      body: detailAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.accent)),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(itemDetailProvider(widget.mediaId)),
        ),
        data: (detail) {
          final meta = detail.metadata;
          final item = detail.item;
          final st = stateAsync[widget.mediaId];
          final hasBackdrop = (meta?.artwork.backdrop ?? item.artwork.backdrop) != null;
          final hasPoster = (meta?.artwork.poster ?? item.artwork.poster) != null;
          final api = ref.watch(apiClientProvider);
          final backdropUrl = api != null && hasBackdrop ? api.artworkUrl(widget.mediaId, 'backdrop') : null;
          final posterUrl = api != null && hasPoster ? api.artworkUrl(widget.mediaId, 'poster') : null;

          final sourceLabel = _sourceLabel(detail);
          final canResume = st?.isResumable == true;

          return Stack(
            children: [
              CustomScrollView(
                slivers: [
                  SliverAppBar(
                    expandedHeight: 400,
                    pinned: true,
                    backgroundColor: AppColors.background,
                    foregroundColor: AppColors.text,
                    title: Text(
                      meta?.title ?? item.title,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.text),
                    ),
                    flexibleSpace: FlexibleSpaceBar(
                      background: Stack(
                        fit: StackFit.expand,
                        children: [
                          if (backdropUrl != null)
                            ImageFiltered(
                              imageFilter: ImageFilter.blur(sigmaX: 34, sigmaY: 34),
                              child: Transform.scale(
                                scale: 1.25,
                                child: CachedNetworkImage(
                                  imageUrl: backdropUrl,
                                  fit: BoxFit.cover,
                                  errorWidget: (_, _, _) => const _BackdropPlaceholder(),
                                ),
                              ),
                            )
                          else
                            const _BackdropPlaceholder(),
                          DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                stops: const [0.0, 0.55, 0.9, 1],
                                colors: [
                                  Colors.black.withValues(alpha: 0.3),
                                  Colors.black.withValues(alpha: 0.45),
                                  AppColors.background.withValues(alpha: 0.92),
                                  AppColors.background,
                                ],
                              ),
                            ),
                          ),
                          SafeArea(
                            bottom: false,
                            child: Align(
                              alignment: Alignment.bottomCenter,
                              child: Padding(
                                padding: const EdgeInsets.fromLTRB(16, 8, 16, 14),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Hero(
                                          tag: 'poster-${widget.mediaId}',
                                          child: ClipRRect(
                                            borderRadius: BorderRadius.circular(12),
                                            child: SizedBox(
                                              width: 104,
                                              height: 156,
                                              child: posterUrl == null
                                                  ? const _SmallPosterPlaceholder()
                                                  : CachedNetworkImage(
                                                      imageUrl: posterUrl,
                                                      fit: BoxFit.cover,
                                                      errorWidget: (_, _, _) => const _SmallPosterPlaceholder(),
                                                    ),
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 14),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                meta?.title ?? item.title,
                                                maxLines: 2,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  color: AppColors.text,
                                                  fontSize: 21,
                                                  fontWeight: FontWeight.w800,
                                                  letterSpacing: -0.3,
                                                  height: 1.15,
                                                  shadows: [Shadow(blurRadius: 6, color: Colors.black)],
                                                ),
                                              ),
                                              const SizedBox(height: 6),
                                              Text(
                                                _metaLine(item, meta),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  color: AppColors.textFaint,
                                                  fontSize: 12.5,
                                                  shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                                                ),
                                              ),
                                              if (meta != null && meta.genres.isNotEmpty) ...[
                                                const SizedBox(height: 10),
                                                Wrap(
                                                  spacing: 6,
                                                  runSpacing: 6,
                                                  children: [
                                                    for (final g in meta.genres.take(3))
                                                      Container(
                                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                                        decoration: BoxDecoration(
                                                          color: Colors.black.withValues(alpha: 0.45),
                                                          borderRadius: BorderRadius.circular(8),
                                                          border: Border.all(color: Colors.white.withValues(alpha: 0.14)),
                                                        ),
                                                        child: Text(
                                                          g,
                                                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                                                        ),
                                                      ),
                                                  ],
                                                ),
                                              ],
                                              if (sourceLabel != null) ...[
                                                const SizedBox(height: 10),
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                                  decoration: BoxDecoration(
                                                    gradient: AppColors.accentGradientFaint,
                                                    borderRadius: BorderRadius.circular(8),
                                                  ),
                                                  child: Text(
                                                    sourceLabel,
                                                    style: const TextStyle(
                                                      color: AppColors.accentBright,
                                                      fontSize: 11,
                                                      fontWeight: FontWeight.w600,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 14),
                                    Row(
                                      children: [
                                        Expanded(
                                          child: _PlayButton(
                                            busy: _busy,
                                            label: canResume ? 'Resume' : 'Play',
                                            onTap: () => playItem(
                                              context,
                                              mediaId: item.mediaId,
                                              title: item.displayTitle,
                                              initialPosition: canResume ? st!.position : 0,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    actions: [
                      PopupMenuButton<String>(
                        icon: const Icon(Icons.more_vert_rounded, color: AppColors.textDim),
                        onSelected: (v) => _handleAction(v, item.mediaId, meta),
                        itemBuilder: (_) => [
                          const PopupMenuItem(value: 'optimize', child: Text('Optimize for streaming')),
                          const PopupMenuItem(value: 'refresh', child: Text('Refresh metadata')),
                          const PopupMenuItem(value: 'watched', child: Text('Mark watched')),
                          const PopupMenuItem(value: 'queue', child: Text('Optimization queue')),
                          const PopupMenuItem(value: 'delete', child: Text('Remove from library')),
                        ],
                      ),
                    ],
                  ),
                  if ((meta?.overview ?? '').isNotEmpty)
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                        child: Text(
                          meta!.overview!,
                          style: const TextStyle(color: AppColors.textDim, fontSize: 13.5, height: 1.55),
                        ),
                      ),
                    ),
                  const SliverToBoxAdapter(child: SizedBox(height: 40)),
                ],
              ),
              if (_busy)
                Positioned.fill(
                  child: Container(
                    color: AppColors.overlay,
                    child: const Center(
                      child: CircularProgressIndicator(color: AppColors.accent),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  String _metaLine(dynamic item, Metadata? meta) {
    final parts = <String>[
      if (meta?.year != null) '${meta!.year}',
      if (meta?.rating != null) '★ ${meta!.rating!.toStringAsFixed(1)}',
      if (meta?.runtime != null) '${meta!.runtime} min',
      if (item.subtitleText.isNotEmpty) item.subtitleText,
    ];
    return parts.join('  ·  ');
  }

  String? _sourceLabel(dynamic detail) {
    final meta = detail.metadata;
    if (meta == null) return null;
    final video = meta.video;
    if (video == null) return null;
    final res = video.height != null ? '${video.height}p' : null;
    final codec = video.codec?.toUpperCase();
    final parts = <String>[
      ?res,
      ?codec,
      if (video.isHdr) 'HDR',
      if (meta.optimization.isDone) 'HLS optimized',
    ];
    return parts.isEmpty ? null : parts.join(' · ');
  }

  Future<void> _handleAction(String action, String mediaId, Metadata? meta) async {
    final api = ref.read(apiClientProvider);
    if (api == null) return;
    setState(() => _busy = true);
    try {
      switch (action) {
        case 'optimize':
          await api.optimize(mediaId, mode: 'hls');
          _toast('Optimization queued');
          ref.invalidate(queueProvider);
        case 'refresh':
          await api.refreshItem(mediaId);
          _toast('Metadata refresh started');
          ref.invalidate(itemDetailProvider(mediaId));
        case 'watched':
          await api.markWatched(mediaId);
          _toast('Marked as watched');
          ref.invalidate(statesProvider);
          ref.invalidate(itemsProvider);
        case 'queue':
          await Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const QueueScreen()),
          );
        case 'delete':
          await _confirmDelete(api, mediaId);
      }
    } catch (e) {
      _toast('Action failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _confirmDelete(ApiClient api, String mediaId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Remove from library?', style: TextStyle(color: AppColors.text, fontSize: 16)),
        content: const Text(
          'This removes the item from your Quark library. The media file is not deleted.',
          style: TextStyle(color: AppColors.textDim, fontSize: 13.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textDim)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Remove', style: TextStyle(color: AppColors.danger)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await api.deleteItem(mediaId);
      if (mounted) Navigator.of(context).pop();
      ref.invalidate(itemsProvider);
      ref.invalidate(showsProvider);
      ref.invalidate(recentProvider);
    }
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..clearSnackBars()
      ..showSnackBar(SnackBar(content: Text(message)));
  }
}

class _BackdropPlaceholder extends StatelessWidget {
  const _BackdropPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      child: const Center(
        child: Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 40),
      ),
    );
  }
}

class _PlayButton extends StatelessWidget {
  final bool busy;
  final String label;
  final VoidCallback onTap;

  const _PlayButton({required this.busy, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        gradient: AppColors.accentGradient,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: AppColors.accent.withValues(alpha: 0.4),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: busy ? null : onTap,
          child: Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (busy)
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.black),
                  )
                else
                  const Icon(Icons.play_arrow_rounded, color: Colors.black, size: 26),
                const SizedBox(width: 8),
                Text(
                  busy ? 'Working…' : label,
                  style: const TextStyle(
                    color: Colors.black,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
        ),
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
        child: Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 26),
      ),
    );
  }
}
