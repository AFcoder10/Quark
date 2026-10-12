class OptimizeJob {
  final String mediaId;
  final String mode;
  final String status;
  final double progress;
  final String message;
  final String? error;
  final String? createdAt;
  final String? finishedAt;

  const OptimizeJob({
    this.mediaId = '',
    this.mode = 'hls',
    this.status = 'queued',
    this.progress = 0,
    this.message = '',
    this.error,
    this.createdAt,
    this.finishedAt,
  });

  factory OptimizeJob.fromJson(Map<String, dynamic> json) {
    return OptimizeJob(
      mediaId: json['media_id'] as String? ?? '',
      mode: json['mode'] as String? ?? 'hls',
      status: json['status'] as String? ?? 'queued',
      progress: (json['progress'] as num?)?.toDouble() ?? 0,
      message: json['message'] as String? ?? '',
      error: json['error'] as String?,
      createdAt: json['created_at'] as String?,
      finishedAt: json['finished_at'] as String?,
    );
  }

  bool get isActive => status == 'queued' || status == 'processing';

  String get statusLabel {
    switch (status) {
      case 'processing':
        return 'Processing';
      case 'queued':
        return 'Queued';
      case 'done':
        return 'Done';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  }
}

class ScanJob {
  final String jobId;
  final String libraryId;
  final String status;
  final String? error;

  const ScanJob({
    this.jobId = '',
    this.libraryId = '',
    this.status = 'queued',
    this.error,
  });

  factory ScanJob.fromJson(Map<String, dynamic> json) {
    return ScanJob(
      jobId: json['job_id'] as String? ?? '',
      libraryId: json['library_id'] as String? ?? '',
      status: json['status'] as String? ?? 'queued',
      error: json['error'] as String?,
    );
  }
}
