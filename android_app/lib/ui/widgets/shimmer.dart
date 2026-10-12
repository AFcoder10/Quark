import 'package:flutter/material.dart';

import '../../theme.dart';

class ShimmerBox extends StatefulWidget {
  final double? width;
  final double? height;
  final BorderRadius borderRadius;

  const ShimmerBox({
    super.key,
    this.width,
    this.height,
    this.borderRadius = const BorderRadius.all(Radius.circular(12)),
  });

  @override
  State<ShimmerBox> createState() => _ShimmerBoxState();
}

class _ShimmerBoxState extends State<ShimmerBox> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1300),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final shift = _controller.value * 2.4;
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius,
            gradient: LinearGradient(
              begin: Alignment(-1.0 + shift, 0),
              end: Alignment(1.0 + shift, 0),
              colors: [
                AppColors.elevated,
                const Color(0xFF333344),
                AppColors.elevated,
              ],
              stops: const [0.25, 0.5, 0.75],
            ),
          ),
        );
      },
    );
  }
}

class PosterGridSkeleton extends StatelessWidget {
  final int count;
  final double childAspectRatio;

  const PosterGridSkeleton({
    super.key,
    this.count = 12,
    this.childAspectRatio = 0.52,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 10,
        mainAxisSpacing: 12,
        childAspectRatio: childAspectRatio,
      ),
      itemCount: count,
      itemBuilder: (_, _) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Expanded(
            child: ShimmerBox(borderRadius: BorderRadius.all(Radius.circular(13))),
          ),
          const SizedBox(height: 8),
          ShimmerBox(
            width: double.infinity,
            height: 11,
            borderRadius: BorderRadius.all(Radius.circular(6)),
          ),
          const SizedBox(height: 6),
          ShimmerBox(
            width: 70,
            height: 10,
            borderRadius: BorderRadius.all(Radius.circular(6)),
          ),
        ],
      ),
    );
  }
}

class BannerSkeleton extends StatelessWidget {
  final double height;

  const BannerSkeleton({super.key, this.height = 210});

  @override
  Widget build(BuildContext context) {
    return ShimmerBox(
      width: double.infinity,
      height: height,
      borderRadius: const BorderRadius.all(Radius.circular(18)),
    );
  }
}

class RowSkeleton extends StatelessWidget {
  final int count;
  final double width;
  final double height;

  const RowSkeleton({
    super.key,
    this.count = 4,
    this.width = 260,
    this.height = 146,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height + 24,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: count,
        separatorBuilder: (_, _) => const SizedBox(width: 12),
        itemBuilder: (_, _) => SizedBox(
          width: width,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ShimmerBox(
                width: width,
                height: height,
                borderRadius: const BorderRadius.all(Radius.circular(14)),
              ),
              const SizedBox(height: 8),
              ShimmerBox(width: width * 0.6, height: 11),
            ],
          ),
        ),
      ),
    );
  }
}
