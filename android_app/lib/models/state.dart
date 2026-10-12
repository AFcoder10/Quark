class PlaybackState {
  final double position;
  final double duration;
  final bool watched;
  final String? lastPlayedAt;

  const PlaybackState({
    this.position = 0,
    this.duration = 0,
    this.watched = false,
    this.lastPlayedAt,
  });

  factory PlaybackState.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const PlaybackState();
    return PlaybackState(
      position: (json['position'] as num?)?.toDouble() ?? 0,
      duration: (json['duration'] as num?)?.toDouble() ?? 0,
      watched: json['watched'] as bool? ?? false,
      lastPlayedAt: json['last_played_at'] as String?,
    );
  }

  bool get isResumable => !watched && position > 30 && (duration <= 0 || position < duration - 30);

  double get progressPct => duration > 0 ? (position / duration) * 100 : 0;
}

class RecentState {
  final String mediaId;
  final double position;
  final double duration;
  final String? lastPlayedAt;
  final double progressPct;

  const RecentState({
    this.mediaId = '',
    this.position = 0,
    this.duration = 0,
    this.lastPlayedAt,
    this.progressPct = 0,
  });

  factory RecentState.fromJson(Map<String, dynamic> json) {
    return RecentState(
      mediaId: json['media_id'] as String? ?? '',
      position: (json['position'] as num?)?.toDouble() ?? 0,
      duration: (json['duration'] as num?)?.toDouble() ?? 0,
      lastPlayedAt: json['last_played_at'] as String?,
      progressPct: (json['progress_pct'] as num?)?.toDouble() ?? 0,
    );
  }
}
