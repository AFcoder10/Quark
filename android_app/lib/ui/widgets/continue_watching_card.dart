import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/item.dart';
import '../../models/state.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import 'shimmer.dart';

class ContinueWatchingCard extends ConsumerWidget {
  final Item item;
  final RecentState state;
  final VoidCallback onPlay;

  const ContinueWatchingCard({
    super.key,
    required this.item,
    required this.state,
    required this.onPlay,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(apiClientProvider);
    final hasBackdrop = item.artwork.backdrop != null;
    final hasPoster = item.artwork.poster != null;
    final hasArt = hasBackdrop || hasPoster;
    final url = api != null && hasArt
        ? api.artworkUrl(item.mediaId, hasBackdrop ? 'backdrop' : 'poster')
        : null;

    return SizedBox(
      width: 280,
      child: GestureDetector(
        onTap: onPlay,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    AspectRatio(
                      aspectRatio: 16 / 9,
                      child: url == null
                          ? const _ThumbPlaceholder()
                          : CachedNetworkImage(
                              imageUrl: url,
                              fit: BoxFit.cover,
                              fadeInDuration: const Duration(milliseconds: 250),
                              placeholder: (_, _) => const ShimmerBox(),
                              errorWidget: (_, _, _) => const _ThumbPlaceholder(),
                            ),
                    ),
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.55),
                            Colors.black.withValues(alpha: 0.85),
                          ],
                          stops: const [0.4, 0.8, 1],
                        ),
                      ),
                    ),
                    Positioned(
                      left: 12,
                      right: 12,
                      bottom: 10,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  item.displayTitle,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 13.5,
                                    fontWeight: FontWeight.w700,
                                    shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Container(
                                width: 34,
                                height: 34,
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.22),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.white.withValues(alpha: 0.5)),
                                ),
                                child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 22),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(2),
                                  child: LinearProgressIndicator(
                                    value: (state.progressPct / 100).clamp(0.0, 1.0),
                                    minHeight: 3,
                                    backgroundColor: Colors.white.withValues(alpha: 0.25),
                                    valueColor: const AlwaysStoppedAnimation(Color(0xFF9D84FF)),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                _formatResume(state.position),
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w500,
                                  shadows: [Shadow(blurRadius: 3, color: Colors.black)],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatResume(double seconds) {
    if (seconds <= 0) return 'Start';
    final h = seconds ~/ 3600;
    final m = ((seconds % 3600) / 60).floor();
    final s = (seconds % 60).floor();
    final time = h > 0
        ? '$h:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}'
        : '$m:${s.toString().padLeft(2, '0')}';
    return time;
  }
}

class _ThumbPlaceholder extends StatelessWidget {
  const _ThumbPlaceholder();

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
      child: const Center(child: Icon(Icons.play_circle_outline, color: AppColors.textFaint, size: 40)),
    );
  }
}
