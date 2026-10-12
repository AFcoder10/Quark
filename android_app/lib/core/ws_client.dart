import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class WsEvent {
  final String type;
  final Map<String, dynamic> data;
  final double ts;

  const WsEvent({required this.type, this.data = const {}, this.ts = 0});

  bool get isScanRelated => type.startsWith('scan.');
  bool get isOptimizeRelated => type.startsWith('optimize.');
  bool get isMetadataRelated => type.startsWith('metadata.');
}

class WsClient {
  final String baseUrl;
  final _events = StreamController<WsEvent>.broadcast();
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  bool _disposed = false;
  bool _manualClose = false;
  int _attempt = 0;

  WsClient(this.baseUrl);

  Stream<WsEvent> get events => _events.stream;

  void connect() {
    _manualClose = false;
    _open();
  }

  void _open() {
    if (_disposed || _manualClose) return;
    final uri = _wsUri();
    try {
      _channel = WebSocketChannel.connect(uri);
    } catch (_) {
      _scheduleReconnect();
      return;
    }
    _channel!.stream.listen(
      (data) => _handleMessage(data),
      onError: (_) => _scheduleReconnect(),
      onDone: () => _scheduleReconnect(),
    );
  }

  void _handleMessage(dynamic data) {
    try {
      final map = jsonDecode(data.toString()) as Map<String, dynamic>;
      final type = map['type'] as String? ?? 'unknown';
      final eventData = map['data'] as Map<String, dynamic>? ?? {};
      final ts = (map['ts'] as num?)?.toDouble() ?? 0;
      if (!_events.isClosed) {
        _events.add(WsEvent(type: type, data: eventData, ts: ts));
      }
    } catch (_) {
      // ignore malformed frames
    }
  }

  Uri _wsUri() {
    final uri = Uri.parse(baseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return Uri(scheme: scheme, host: uri.host, port: uri.port, path: '/ws');
  }

  void _scheduleReconnect() {
    if (_disposed || _manualClose) return;
    _attempt++;
    final delay = Duration(milliseconds: (3000 * _attempt.clamp(1, 10)).clamp(3000, 30000));
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      _attempt = 0;
      _open();
    });
  }

  void close() {
    _manualClose = true;
    _disposed = true;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _events.close();
  }
}
