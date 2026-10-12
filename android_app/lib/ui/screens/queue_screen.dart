import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/queue.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../widgets/empty_state.dart';
import '../widgets/state_views.dart';

class QueueScreen extends ConsumerWidget {
  const QueueScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueAsync = ref.watch(queueProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Optimization Queue'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(queueProvider),
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textDim, size: 22),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: queueAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(message: e.toString(), onRetry: () => ref.invalidate(queueProvider)),
        data: (jobs) {
          if (jobs.isEmpty) {
            return const EmptyState(
              icon: Icons.done_all_rounded,
              title: 'Nothing in the queue',
              subtitle: 'Optimize an item from its detail page to transcode it into a streaming-friendly HLS format.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: jobs.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) => _JobCard(job: jobs[i]),
          );
        },
      ),
    );
  }
}

class _JobCard extends ConsumerWidget {
  final OptimizeJob job;
  const _JobCard({required this.job});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final active = job.isActive;
    final color = _statusColor(job.status);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(_statusIcon(job.status), color: color, size: 18),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _title(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: AppColors.text, fontSize: 14, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${job.mode.toUpperCase()}  ·  ${job.statusLabel}',
                      style: TextStyle(color: AppColors.textFaint, fontSize: 11.5),
                    ),
                  ],
                ),
              ),
              if (active)
                IconButton(
                  tooltip: 'Cancel',
                  onPressed: () {
                    final api = ref.read(apiClientProvider);
                    if (api == null) return;
                    api.cancelOptimize(job.mediaId);
                    ref.invalidate(queueProvider);
                    ref.invalidate(itemsProvider);
                  },
                  icon: const Icon(Icons.close_rounded, color: AppColors.textFaint, size: 20),
                ),
            ],
          ),
          if (job.status == 'processing' || job.progress > 0) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (job.progress / 100).clamp(0.0, 1.0),
                minHeight: 5,
                backgroundColor: AppColors.elevated,
                valueColor: AlwaysStoppedAnimation(color),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '${(job.progress * 10).round() / 10}%  ${job.message}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.textFaint, fontSize: 11),
            ),
          ],
          if (job.status == 'failed' && job.error != null) ...[
            const SizedBox(height: 8),
            Text(
              job.error!,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.danger, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  String _title() {
    final display = job.mediaId.length > 40
        ? '${job.mediaId.substring(0, 40)}…'
        : job.mediaId;
    return display;
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'processing':
        return AppColors.accent;
      case 'queued':
        return AppColors.warning;
      case 'done':
        return AppColors.success;
      case 'failed':
        return AppColors.danger;
      default:
        return AppColors.textFaint;
    }
  }

  IconData _statusIcon(String status) {
    switch (status) {
      case 'processing':
        return Icons.autorenew_rounded;
      case 'queued':
        return Icons.schedule_rounded;
      case 'done':
        return Icons.check_circle_outline;
      case 'failed':
        return Icons.error_outline;
      default:
        return Icons.hourglass_empty_rounded;
    }
  }
}
