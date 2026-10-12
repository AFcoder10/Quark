import 'package:shared_preferences/shared_preferences.dart';

class ServerProfile {
  final String url;
  final String name;
  final DateTime savedAt;

  const ServerProfile({required this.url, required this.name, required this.savedAt});

  String get host {
    final uri = Uri.tryParse(url);
    return uri?.host ?? url;
  }
}

class AppSettings {
  static const _kServerUrl = 'server_url';
  static const _kServerName = 'server_name';
  static const _kAllow4k = 'allow_4k';
  static const _kCellularEnabled = 'cellular_enabled';
  static const _kAutoResume = 'auto_resume';

  String? serverUrl;
  String? serverName;
  bool allow4k = true;
  bool cellularEnabled = false;
  bool autoResume = true;
  bool loaded = false;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    serverUrl = prefs.getString(_kServerUrl);
    serverName = prefs.getString(_kServerName);
    allow4k = prefs.getBool(_kAllow4k) ?? true;
    cellularEnabled = prefs.getBool(_kCellularEnabled) ?? false;
    autoResume = prefs.getBool(_kAutoResume) ?? true;
    loaded = true;
  }

  Future<void> setServer(String url, {String? name}) async {
    serverUrl = url;
    serverName = name;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kServerUrl, url);
    await prefs.setString(_kServerName, name ?? '');
  }

  Future<void> setAllow4k(bool value) async {
    allow4k = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kAllow4k, value);
  }

  Future<void> setCellularEnabled(bool value) async {
    cellularEnabled = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kCellularEnabled, value);
  }

  Future<void> setAutoResume(bool value) async {
    autoResume = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kAutoResume, value);
  }

  Future<void> clear() async {
    serverUrl = null;
    serverName = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kServerUrl);
    await prefs.remove(_kServerName);
  }
}

/// Normalizes user input into a full server URL.
String normalizeServerUrl(String input) {
  var value = input.trim();
  if (value.isEmpty) return value;
  if (!value.startsWith('http://') && !value.startsWith('https://')) {
    value = 'http://$value';
  }
  while (value.endsWith('/')) {
    value = value.substring(0, value.length - 1);
  }
  return value;
}
