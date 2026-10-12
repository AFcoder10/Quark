class Health {
  final String status;
  final String version;
  final int items;
  final int libraries;

  const Health({
    this.status = 'unknown',
    this.version = '0.0.0',
    this.items = 0,
    this.libraries = 0,
  });

  factory Health.fromJson(Map<String, dynamic> json) {
    return Health(
      status: json['status'] as String? ?? 'unknown',
      version: json['version'] as String? ?? '0.0.0',
      items: (json['items'] as num?)?.toInt() ?? 0,
      libraries: (json['libraries'] as num?)?.toInt() ?? 0,
    );
  }

  bool get isOk => status == 'ok';
}
