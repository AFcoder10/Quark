import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';

class MiniPlayerBar extends ConsumerWidget {
  const MiniPlayerBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final np = ref.watch(nowPlayingProvider);
    final api = ref.watch(apiClientProvider);
    if (np == null) return const SizedBox.shrink();

    final thumb = api?.artworkUrl(np.mediaId, 'backdrop');

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border.withValues(alpha: 0.6))),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.4),
            blurRadius: 14,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        bottom: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            GestureDetector(
              onTap: () => playItem(
                context,
                mediaId: np.mediaId,
                title: np.title,
                initialPosition: np.position,
              ),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(10, 8, 6, 8),
                child: Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: SizedBox(
                        width: 74,
                        height: 42,
                        child: thumb == null
                            ? Container(
                                color: AppColors.elevated,
                                child: const Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 18),
                              )
                            : CachedNetworkImage(
                                imageUrl: thumb,
                                fit: BoxFit.cover,
                                errorWidget: (_, _, _) => Container(
                                  color: AppColors.elevated,
                                  child: const Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 18),
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            np.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.text,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 5),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(2),
                            child: LinearProgressIndicator(
                              value: (np.progressPct / 100).clamp(0.0, 1.0),
                              minHeight: 3,
                              backgroundColor: Colors.white.withValues(alpha: 0.12),
                              valueColor: const AlwaysStoppedAnimation(Color(0xFF9D84FF)),
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: 'Resume',
                      onPressed: () => playItem(
                        context,
                        mediaId: np.mediaId,
                        title: np.title,
                        initialPosition: np.position,
                      ),
                      icon: const Icon(Icons.play_arrow_rounded, color: AppColors.accentBright, size: 26),
                    ),
                    IconButton(
                      tooltip: 'Dismiss',
                      onPressed: () => ref.read(nowPlayingProvider.notifier).dismiss(),
                      icon: const Icon(Icons.close_rounded, color: AppColors.textFaint, size: 20),
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
}
