import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/show.dart';
import '../../providers/providers.dart';
import '../../theme.dart';

class ShowCard extends ConsumerWidget {
  final Show show;
  final VoidCallback onTap;

  const ShowCard({super.key, required this.show, required this.onTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(apiClientProvider);
    final poster = show.artworkUrls.poster;
    final url = api != null && poster != null ? api.resolveUrl(poster) : null;

    return GestureDetector(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(13),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  url == null
                      ? const _ShowPlaceholder()
                      : CachedNetworkImage(
                          imageUrl: url,
                          fit: BoxFit.cover,
                          fadeInDuration: const Duration(milliseconds: 200),
                          placeholder: (_, _) => const _ShowPlaceholder(),
                          errorWidget: (_, _, _) => const _ShowPlaceholder(),
                        ),
                  Positioned(
                    right: 6,
                    top: 6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.movie_outlined, color: AppColors.accentBright, size: 11),
                          const SizedBox(width: 3),
                          Text(
                            '${show.episodeCount}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            show.seriesTitle,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (show.year != null)
            Text(
              '${show.year}',
              style: const TextStyle(color: AppColors.textFaint, fontSize: 11),
            ),
        ],
      ),
    );
  }
}

class _ShowPlaceholder extends StatelessWidget {
  const _ShowPlaceholder();

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
      child: const Center(
        child: Icon(Icons.live_tv_outlined, color: AppColors.textFaint, size: 30),
      ),
    );
  }
}
