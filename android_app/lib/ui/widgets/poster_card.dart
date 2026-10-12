import 'dart:math' as math;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/item.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import 'shimmer.dart';

class PosterCard extends ConsumerStatefulWidget {
  final Item item;
  final String? artworkUrl;
  final double? progress;
  final bool watched;
  final bool compact;
  final String? heroTag;
  final VoidCallback? onTap;

  const PosterCard({
    super.key,
    required this.item,
    this.artworkUrl,
    this.progress,
    this.watched = false,
    this.compact = false,
    this.heroTag,
    this.onTap,
  });

  @override
  ConsumerState<PosterCard> createState() => _PosterCardState();
}

class _PosterCardState extends ConsumerState<PosterCard> {
  bool _pressed = false;

  void _setPressed(bool value) {
    if (_pressed != value) setState(() => _pressed = value);
  }

  @override
  Widget build(BuildContext context) {
    final api = ref.watch(apiClientProvider);
    final item = widget.item;
    final hasPoster = item.artwork.poster != null;
    final url = widget.artworkUrl ??
        (api != null && hasPoster ? api.artworkUrl(item.mediaId, 'poster') : null);

    final progress = widget.progress;
    final showProgress = !widget.watched && progress != null && progress > 0 && progress < 99.5;

    final radius = BorderRadius.circular(widget.compact ? 10 : 14);

    Widget poster = ClipRRect(
      borderRadius: radius,
      child: Stack(
        fit: StackFit.expand,
        children: [
          _PosterImage(url: url, title: item.displayTitle, radius: radius),
          if (widget.watched)
            Container(
              color: Colors.black.withValues(alpha: 0.45),
              child: const Center(
                child: Icon(Icons.check_circle, color: AppColors.success, size: 30),
              ),
            ),
          if (item.optimized)
            Positioned(
              top: 6,
              left: 6,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                decoration: BoxDecoration(
                  gradient: AppColors.accentGradient,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'HLS',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ),
          if (showProgress)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: Container(
                height: 44,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.bottomCenter,
                    end: Alignment.topCenter,
                    colors: [
                      Colors.black.withValues(alpha: 0.7),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
            ),
          if (showProgress)
            Positioned(
              left: 0,
              right: 0,
              bottom: 8,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(2),
                        child: LinearProgressIndicator(
                          value: (progress / 100).clamp(0.0, 1.0),
                          minHeight: 3,
                          backgroundColor: Colors.white.withValues(alpha: 0.22),
                          valueColor: const AlwaysStoppedAnimation(Color(0xFF9D84FF)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    _ProgressRing(value: (progress / 100).clamp(0.0, 1.0), size: 16),
                  ],
                ),
              ),
            ),
          if (showProgress)
            Center(
              child: Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.45),
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white.withValues(alpha: 0.5)),
                ),
                child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 22),
              ),
            ),
        ],
      ),
    );

    if (widget.heroTag != null) {
      poster = Hero(tag: widget.heroTag!, child: poster);
    }

    return GestureDetector(
      onTapDown: (_) => _setPressed(true),
      onTapUp: (_) => _setPressed(false),
      onTapCancel: () => _setPressed(false),
      onTap: widget.onTap,
      child: AnimatedScale(
        scale: _pressed ? 0.955 : 1.0,
        duration: const Duration(milliseconds: 110),
        curve: Curves.easeOut,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: radius,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.35),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: poster,
              ),
            ),
            SizedBox(height: widget.compact ? 4 : 7),
            Text(
              item.displayTitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: widget.compact ? 11.5 : 12.5,
                fontWeight: FontWeight.w600,
                color: AppColors.text,
                height: 1.15,
              ),
            ),
            if (item.subtitleText.isNotEmpty)
              Text(
                item.subtitleText,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: widget.compact ? 10 : 11,
                  color: AppColors.textFaint,
                  height: 1.2,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ProgressRing extends StatelessWidget {
  final double value;
  final double size;

  const _ProgressRing({required this.value, required this.size});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _RingPainter(value: value)),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double value;

  _RingPainter({required this.value});

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = size.width / 2 - 1.5;
    final track = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4
      ..color = Colors.white.withValues(alpha: 0.35);
    canvas.drawCircle(center, radius, track);
    final v = value.clamp(0.0, 1.0);
    if (v <= 0.005) return;
    final arc = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4
      ..strokeCap = StrokeCap.round
      ..shader = AppColors.accentGradient
          .createShader(Rect.fromCircle(center: center, radius: radius));
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      2 * math.pi * v,
      false,
      arc,
    );
  }

  @override
  bool shouldRepaint(_RingPainter oldDelegate) => oldDelegate.value != value;
}

class _PosterImage extends StatelessWidget {
  final String? url;
  final String title;
  final BorderRadius radius;

  const _PosterImage({required this.url, required this.title, required this.radius});

  @override
  Widget build(BuildContext context) {
    if (url == null || url!.isEmpty) {
      return const _Placeholder();
    }
    return CachedNetworkImage(
      imageUrl: url!,
      fit: BoxFit.cover,
      fadeInDuration: const Duration(milliseconds: 250),
      placeholder: (_, _) => ShimmerBox(borderRadius: radius),
      errorWidget: (_, _, _) => const _Placeholder(),
    );
  }
}

class _Placeholder extends StatelessWidget {
  const _Placeholder();

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
        child: Icon(Icons.movie_outlined, color: AppColors.textFaint, size: 30),
      ),
    );
  }
}
