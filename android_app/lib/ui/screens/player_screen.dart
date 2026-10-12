import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import '../../core/api_client.dart';
import '../../models/metadata.dart';
import '../../providers/providers.dart';
import '../../theme.dart';

enum _PlayMode { direct, hls, transcode, auto }

class PlayerScreen extends ConsumerStatefulWidget {
  final String mediaId;
  final String title;
  final double initialPosition;

  const PlayerScreen({
    super.key,
    required this.mediaId,
    required this.title,
    this.initialPosition = 0,
  });

  @override
  ConsumerState<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends ConsumerState<PlayerScreen> {
  VideoPlayerController? _controller;
  Metadata? _meta;
  bool _initializing = true;
  String? _error;
  _PlayMode _mode = _PlayMode.auto;
  bool _controlsVisible = true;
  Timer? _hideTimer;
  Timer? _progressTimer;
  double _speed = 1.0;
  bool _markedWatched = false;
  double _lastSavedPosition = 0;
  int? _resHeight;
  SubtitleTrack? _activeSubtitle;
  List<_SubCue> _subCues = const [];
  String _subText = '';
  Timer? _subtitleTimer;

  @override
  void initState() {
    super.initState();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    _setup();
  }

  Future<void> _setup() async {
    final api = ref.read(apiClientProvider);
    if (api == null) {
      setState(() { _initializing = false; _error = 'No server configured'; });
      return;
    }
    try {
      final detail = await api.itemDetail(widget.mediaId);
      final meta = detail.metadata;
      setState(() { _meta = meta; });
      SubtitleTrack? defSub;
      for (final s in meta?.subtitles ?? const <SubtitleTrack>[]) {
        if (s.isDefault) { defSub = s; break; }
      }
      if (defSub?.index != null) _selectSubtitle(defSub!);
    } catch (_) {}

    final meta = _meta;
    if (meta == null) {
      await _playTranscode(api);
      return;
    }
    final isOptimized = meta.optimization.isDone && meta.optimization.status == 'done';
    if (isOptimized) {
      await _play(api.hlsUrl(widget.mediaId), _PlayMode.hls, api);
    } else if (meta.playback.directPlaySupported) {
      final ok = await _tryDirect(api);
      if (!ok) await _playTranscode(api);
    } else {
      await _playTranscode(api);
    }
  }

  Future<bool> _tryDirect(ApiClient api) async {
    try {
      await _play(api.directUrl(widget.mediaId), _PlayMode.direct, api);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> _playTranscode(ApiClient api, {double? start}) async {
    final allow4k = ref.read(settingsProvider).allow4k;
    final height = _resHeight ?? (allow4k ? 2160 : 1080);
    final url = api.transcodeUrl(widget.mediaId, height: height, start: start ?? widget.initialPosition);
    try {
      await _play(url, _PlayMode.transcode, api);
    } catch (e) {
      if (mounted) {
        setState(() {
          _initializing = false;
          _error = 'Unable to play this item: $e';
        });
      }
    }
  }

  Future<void> _play(String url, _PlayMode mode, ApiClient api) async {
    final controller = VideoPlayerController.networkUrl(Uri.parse(url));
    try {
      await controller.initialize();
      if (!mounted) { controller.dispose(); return; }
      setState(() {
        _controller = controller;
        _mode = mode;
        _initializing = false;
        _error = null;
      });
      if (widget.initialPosition > 0 && mode != _PlayMode.transcode) {
        controller.seekTo(Duration(milliseconds: (widget.initialPosition * 1000).round()));
      }
      controller.play();
      ref.read(nowPlayingProvider.notifier).setSession(widget.mediaId, widget.title);
      await WakelockPlus.enable();
      _startTimers();
      _hideControls();
    } catch (e) {
      controller.dispose();
      rethrow;
    }
  }

  Future<void> _switchMode(_PlayMode mode) async {
    setState(() { _initializing = true; _error = null; });
    final api = ref.read(apiClientProvider)!;
    final controller = _controller;
    final resume = controller != null && controller.value.isInitialized
        ? controller.value.position.inMilliseconds / 1000
        : widget.initialPosition;

    if (controller != null) {
      await _saveProgressNow();
      controller.dispose();
      _controller = null;
    }

    setState(() { _mode = mode; });

    try {
      switch (mode) {
        case _PlayMode.direct:
          await _tryDirect(api);
          break;
        case _PlayMode.hls:
          final meta = _meta;
          if (meta == null || !meta.optimization.isDone) {
            setState(() { _initializing = false; _error = 'HLS not available for this item'; });
            return;
          }
          await _play(api.hlsUrl(widget.mediaId), _PlayMode.hls, api);
          break;
        case _PlayMode.transcode:
          await _playTranscode(api, start: resume);
          break;
        case _PlayMode.auto:
          await _setup();
          break;
      }
    } catch (e) {
      setState(() { _initializing = false; _error = '$e'; });
    }
  }

  Future<void> _changeResolution(int? height) async {
    if (_resHeight == height) return;
    setState(() { _resHeight = height; });
    if (_mode != _PlayMode.transcode) return;

    setState(() { _initializing = true; _error = null; });
    final api = ref.read(apiClientProvider)!;
    final controller = _controller;
    final resume = controller != null && controller.value.isInitialized
        ? controller.value.position.inMilliseconds / 1000
        : widget.initialPosition;
    if (controller != null) {
      await _saveProgressNow();
      controller.dispose();
      _controller = null;
    }
    try {
      await _playTranscode(api, start: resume);
    } catch (e) {
      if (mounted) setState(() { _initializing = false; _error = '$e'; });
    }
  }

  Future<void> _selectSubtitle(SubtitleTrack? track) async {
    _subtitleTimer?.cancel();
    _subtitleTimer = null;
    setState(() {
      _activeSubtitle = track;
      _subText = '';
      _subCues = const [];
    });
    if (track == null || track.index == null) return;
    final api = ref.read(apiClientProvider);
    if (api == null) return;
    try {
      final vtt = await api.subtitleFile(widget.mediaId, track.index!);
      final cues = _parseVtt(vtt);
      if (!mounted) return;
      setState(() { _subCues = cues; });
      _subtitleTimer = Timer.periodic(const Duration(milliseconds: 200), (_) => _subtitleTick());
    } catch (_) {}
  }

  void _subtitleTick() {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized || _subCues.isEmpty) return;
    final posMs = controller.value.position.inMilliseconds;
    String? match;
    for (final cue in _subCues) {
      if (posMs >= cue.start && posMs <= cue.end) { match = cue.text; break; }
    }
    final text = match ?? '';
    if (text != _subText && mounted) {
      setState(() { _subText = text; });
    }
  }

  void _startTimers() {
    _progressTimer?.cancel();
    _progressTimer = Timer.periodic(const Duration(seconds: 10), (_) => _saveProgressNow());
  }

  Future<void> _saveProgressNow() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    final pos = controller.value.position.inMilliseconds / 1000;
    final dur = controller.value.duration.inMilliseconds / 1000;
    ref.read(nowPlayingProvider.notifier).update(
      position: pos,
      duration: dur,
      playing: controller.value.isPlaying,
    );
    if ((pos - _lastSavedPosition).abs() < 2) return;
    _lastSavedPosition = pos;
    final api = ref.read(apiClientProvider);
    if (api == null) return;
    try {
      await api.saveProgress(widget.mediaId, pos, dur);
      if (dur > 0 && pos / dur >= 0.9 && !_markedWatched) {
        _markedWatched = true;
        await api.markWatched(widget.mediaId);
        ref.invalidate(statesProvider);
        ref.invalidate(recentProvider);
      }
    } catch (_) {}
  }

  void _showControls() {
    setState(() => _controlsVisible = true);
    _hideTimer?.cancel();
    _hideTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && (_controller?.value.isPlaying ?? false)) {
        setState(() => _controlsVisible = false);
      }
    });
  }

  void _hideControls() {
    _hideTimer?.cancel();
    _hideTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && (_controller?.value.isPlaying ?? false)) {
        setState(() => _controlsVisible = false);
      }
    });
  }

  void _togglePlay() {
    final c = _controller;
    if (c == null) return;
    final wasPlaying = c.value.isPlaying;
    wasPlaying ? c.pause() : c.play();
    ref.read(nowPlayingProvider.notifier).update(playing: !wasPlaying);
    _showControls();
  }

  void _seekBy(Duration delta) {
    final c = _controller;
    if (c == null) return;
    final target = c.value.position + delta;
    c.seekTo(target < Duration.zero ? Duration.zero : target);
    _showControls();
  }

  Future<void> _seekTo(double fraction) async {
    final c = _controller;
    if (c == null) return;
    final dur = c.value.duration;
    await c.seekTo(Duration(milliseconds: (dur.inMilliseconds * fraction).round()));
    _showControls();
  }

  void _setSpeed(double speed) {
    _controller?.setPlaybackSpeed(speed);
    setState(() => _speed = speed);
    _showControls();
  }

  @override
  void dispose() {
    _progressTimer?.cancel();
    _hideTimer?.cancel();
    _subtitleTimer?.cancel();
    final controller = _controller;
    if (controller != null && controller.value.isInitialized) {
      final pos = controller.value.position.inMilliseconds / 1000;
      final dur = controller.value.duration.inMilliseconds / 1000;
      ref.read(nowPlayingProvider.notifier).update(position: pos, duration: dur, playing: false);
    } else {
      ref.read(nowPlayingProvider.notifier).stop();
    }
    _saveProgressNow();
    _controller?.dispose();
    WakelockPlus.disable();
    SystemChrome.setPreferredOrientations(DeviceOrientation.values);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: _controlsVisible ? _hideControls : _showControls,
        child: Stack(
          children: [
            Positioned.fill(
              child: _initializing
                  ? const _LoadingIndicator()
                  : _error != null
                      ? _ErrorView(message: _error!)
                      : _buildVideo(),
            ),
            if (_controller != null && _controlsVisible)
              _buildControlsOverlay(),
            if (_controller == null)
              SafeArea(
                child: Align(
                  alignment: Alignment.topLeft,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: IconButton(
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 26),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideo() {
    final controller = _controller!;
    return Center(
      child: AspectRatio(
        aspectRatio: controller.value.aspectRatio,
        child: Stack(
          fit: StackFit.expand,
          children: [
            VideoPlayer(controller),
            if (_subText.isNotEmpty)
              Positioned(
                left: 0,
                right: 0,
                bottom: 32,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Text(
                    _subText,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 21,
                      height: 1.35,
                      fontWeight: FontWeight.w500,
                      shadows: [
                        Shadow(blurRadius: 8, color: Colors.black, offset: Offset(0, 2)),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlsOverlay() {
    final value = _controller!.value;
    final duration = value.duration;
    final position = value.position;
    final fraction = duration.inMilliseconds > 0
        ? (position.inMilliseconds / duration.inMilliseconds).clamp(0.0, 1.0)
        : 0.0;

    return Positioned.fill(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Colors.black.withValues(alpha: 0.7),
              Colors.transparent,
              Colors.black.withValues(alpha: 0.85),
            ],
            stops: const [0, 0.35, 1],
          ),
        ),
        child: Column(
          children: [
            SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      iconSize: 22,
                      color: Colors.white,
                      icon: const Icon(Icons.arrow_back_rounded),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        widget.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    if (_mode == _PlayMode.transcode) ...[
                      _ResolutionMenu(height: _resHeight, onChanged: _changeResolution),
                      const SizedBox(width: 6),
                    ],
                    _QualityMenu(
                      mode: _mode,
                      isOptimized: _meta?.optimization.isDone == true,
                      isDirectAvailable: _meta?.playback.directPlaySupported == true,
                      allow4k: ref.read(settingsProvider).allow4k,
                      onSelect: _switchMode,
                    ),
                    if ((_meta?.subtitles ?? const <SubtitleTrack>[]).isNotEmpty) ...[
                      const SizedBox(width: 6),
                      _SubtitleMenu(
                        tracks: _meta!.subtitles,
                        active: _activeSubtitle,
                        onSelect: _selectSubtitle,
                      ),
                    ],
                    const SizedBox(width: 6),
                    _SpeedMenu(speed: _speed, onChanged: _setSpeed),
                  ],
                ),
              ),
            ),
            const Spacer(),
            SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        activeTrackColor: AppColors.accent,
                        inactiveTrackColor: Colors.white.withValues(alpha: 0.25),
                        thumbColor: AppColors.accent,
                        overlayColor: AppColors.accent.withValues(alpha: 0.2),
                        trackHeight: 3,
                      ),
                      child: Slider(
                        value: fraction,
                        onChanged: _seekTo,
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _fmt(position),
                          style: const TextStyle(color: Colors.white70, fontSize: 12, fontFeatures: [FontFeature.tabularFigures()]),
                        ),
                        Text(
                          _fmt(duration),
                          style: const TextStyle(color: Colors.white70, fontSize: 12, fontFeatures: [FontFeature.tabularFigures()]),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      IconButton(
                        onPressed: () => _seekBy(const Duration(seconds: -10)),
                        iconSize: 34,
                        color: Colors.white,
                        icon: const Icon(Icons.replay_10_rounded),
                      ),
                      const SizedBox(width: 24),
                      Container(
                        width: 62,
                        height: 62,
                        decoration: BoxDecoration(
                          color: AppColors.accent,
                          shape: BoxShape.circle,
                          boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.4), blurRadius: 20)],
                        ),
                        child: IconButton(
                          onPressed: _togglePlay,
                          iconSize: 36,
                          color: Colors.white,
                          icon: Icon(value.isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded),
                        ),
                      ),
                      const SizedBox(width: 24),
                      IconButton(
                        onPressed: () => _seekBy(const Duration(seconds: 10)),
                        iconSize: 34,
                        color: Colors.white,
                        icon: const Icon(Icons.forward_10_rounded),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _fmt(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes.remainder(60);
    final s = d.inSeconds.remainder(60);
    return h > 0
        ? '$h:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}'
        : '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }
}

class _SubCue {
  final int start;
  final int end;
  final String text;

  const _SubCue(this.start, this.end, this.text);
}

List<_SubCue> _parseVtt(String raw) {
  final cues = <_SubCue>[];
  final lines = raw.split(RegExp(r'\r?\n'));
  String? timing;
  final buffer = <String>[];
  void flush() {
    if (timing != null && buffer.isNotEmpty) {
      final t = _parseTiming(timing!);
      if (t != null) {
        cues.add(_SubCue(t.$1, t.$2, buffer.join('\n').trim()));
      }
    }
    timing = null;
    buffer.clear();
  }

  for (final line in lines) {
    if (line.contains('-->')) {
      flush();
      timing = line;
    } else if (line.trim().isEmpty) {
      flush();
    } else if (timing != null) {
      buffer.add(line.replaceAll(RegExp(r'<[^>]+>'), ''));
    }
  }
  flush();
  return cues;
}

(int, int)? _parseTiming(String line) {
  final m = RegExp(
    r'(\d+:\d+:\d+[.,]\d+|\d+:\d+[.,]\d+)\s*-->\s*(\d+:\d+:\d+[.,]\d+|\d+:\d+[.,]\d+)',
  ).firstMatch(line);
  if (m == null) return null;
  return (_tsToMs(m.group(1)!), _tsToMs(m.group(2)!));
}

int _tsToMs(String s) {
  final parts = s.replaceAll(',', '.').split(':');
  final secMs = double.parse(parts.removeLast());
  var minutes = 0;
  var hours = 0;
  if (parts.isNotEmpty) minutes = int.parse(parts.removeLast());
  if (parts.isNotEmpty) hours = int.parse(parts.removeLast());
  return ((hours * 60 + minutes) * 60) * 1000 + (secMs * 1000).round();
}

class _QualityMenu extends StatelessWidget {
  final _PlayMode mode;
  final bool isOptimized;
  final bool isDirectAvailable;
  final bool allow4k;
  final Future<void> Function(_PlayMode) onSelect;

  const _QualityMenu({
    required this.mode,
    required this.isOptimized,
    required this.isDirectAvailable,
    required this.allow4k,
    required this.onSelect,
  });

  String _modeLabel(_PlayMode m) {
    switch (m) {
      case _PlayMode.auto:
        return isOptimized ? 'Auto (HLS)' : 'Auto';
      case _PlayMode.direct:
        return 'Direct';
      case _PlayMode.hls:
        return 'HLS Adaptive';
      case _PlayMode.transcode:
        return 'Transcode';
    }
  }

  IconData _modeIcon(_PlayMode m) {
    switch (m) {
      case _PlayMode.auto:
        return Icons.auto_awesome_rounded;
      case _PlayMode.direct:
        return Icons.play_circle_outline;
      case _PlayMode.hls:
        return Icons.equalizer_rounded;
      case _PlayMode.transcode:
        return Icons.sync_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = <_PlayMode>[
      _PlayMode.auto,
      if (isDirectAvailable) _PlayMode.direct,
      if (isOptimized) _PlayMode.hls,
      _PlayMode.transcode,
    ];
    if (items.isEmpty) return const SizedBox.shrink();

    return PopupMenuButton<_PlayMode>(
      initialValue: mode,
      offset: const Offset(0, 48),
      color: Colors.black87,
      onSelected: (m) {
        if (m != mode) onSelect(m);
      },
      icon: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          _modeLabel(mode),
          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
        ),
      ),
      itemBuilder: (_) => items.map((m) => PopupMenuItem(
        value: m,
        child: Row(
          children: [
            Icon(_modeIcon(m), color: m == mode ? AppColors.accentBright : Colors.white70, size: 16),
            const SizedBox(width: 8),
            Text(_modeLabel(m), style: TextStyle(color: m == mode ? Colors.white : Colors.white70, fontSize: 13)),
            if (m == mode) ...[const Spacer(), const Icon(Icons.check, color: AppColors.accent, size: 14)],
          ],
        ),
      )).toList(),
    );
  }
}

class _SpeedMenu extends StatelessWidget {
  final double speed;
  final ValueChanged<double> onChanged;

  const _SpeedMenu({required this.speed, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<double>(
      initialValue: speed,
      color: Colors.black87,
      offset: const Offset(0, 40),
      onSelected: onChanged,
      icon: Text(
        speed == 1.0 ? '1x' : '${speed}x',
        style: const TextStyle(color: Colors.white, fontSize: 12.5, fontWeight: FontWeight.w700),
      ),
      itemBuilder: (_) => [
        for (final s in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
          PopupMenuItem(
            value: s,
            child: Row(
              children: [
                Text('${s}x', style: TextStyle(color: speed == s ? Colors.white : Colors.white70, fontSize: 13.5)),
                if (speed == s) ...[const Spacer(), const Icon(Icons.check, color: AppColors.accent, size: 14)],
              ],
            ),
          ),
      ],
    );
  }
}

class _SubtitleMenu extends StatelessWidget {
  final List<SubtitleTrack> tracks;
  final SubtitleTrack? active;
  final ValueChanged<SubtitleTrack?> onSelect;

  const _SubtitleMenu({required this.tracks, required this.active, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<Object?>(
      color: Colors.black87,
      offset: const Offset(0, 40),
      onSelected: (v) => onSelect(v == null ? null : v as SubtitleTrack),
      icon: Icon(
        active == null ? Icons.subtitles_off_rounded : Icons.subtitles_rounded,
        color: active == null ? Colors.white70 : AppColors.accentBright,
        size: 20,
      ),
      itemBuilder: (_) => [
        PopupMenuItem<Object?>(
          value: null,
          child: Row(
            children: [
              Icon(Icons.subtitles_off_rounded,
                  color: active == null ? AppColors.accentBright : Colors.white70, size: 16),
              const SizedBox(width: 8),
              Text('Off', style: TextStyle(color: active == null ? Colors.white : Colors.white70, fontSize: 13)),
              if (active == null) ...[
                const Spacer(),
                const Icon(Icons.check, color: AppColors.accent, size: 14),
              ],
            ],
          ),
        ),
        for (final t in tracks)
          PopupMenuItem<Object?>(
            value: t,
            child: Row(
              children: [
                Icon(Icons.subtitles_rounded,
                    color: active?.index == t.index ? AppColors.accentBright : Colors.white70, size: 16),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    t.label,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: active?.index == t.index ? Colors.white : Colors.white70, fontSize: 13),
                  ),
                ),
                if (active?.index == t.index) ...[
                  const Spacer(),
                  const Icon(Icons.check, color: AppColors.accent, size: 14),
                ],
              ],
            ),
          ),
      ],
    );
  }
}

class _ResolutionMenu extends StatelessWidget {
  final int? height;
  final ValueChanged<int?> onChanged;

  const _ResolutionMenu({required this.height, required this.onChanged});

  String get _label {
    if (height == null) return 'Auto';
    return height! >= 2000 ? '4K' : '${height}p';
  }

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<int?>(
      initialValue: height,
      color: Colors.black87,
      offset: const Offset(0, 40),
      onSelected: onChanged,
      icon: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          _label,
          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
        ),
      ),
      itemBuilder: (_) => [
        for (final h in [null, 720, 1080, 2160])
          PopupMenuItem<int?>(
            value: h,
            child: Row(
              children: [
                Text(
                  h == null ? 'Auto' : (h >= 2000 ? '4K (2160p)' : '${h}p'),
                  style: TextStyle(color: height == h ? Colors.white : Colors.white70, fontSize: 13),
                ),
                if (height == h) ...[
                  const Spacer(),
                  const Icon(Icons.check, color: AppColors.accent, size: 14),
                ],
              ],
            ),
          ),
      ],
    );
  }
}

class _LoadingIndicator extends StatelessWidget {
  const _LoadingIndicator();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: AppColors.accent, strokeWidth: 3),
          SizedBox(height: 16),
          Text('Connecting…', style: TextStyle(color: AppColors.textDim, fontSize: 13)),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  const _ErrorView({required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppColors.danger, size: 44),
            const SizedBox(height: 14),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textDim, fontSize: 13.5, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}
