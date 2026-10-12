class Library {
  final String id;
  final String name;
  final String path;
  final String type;
  final bool enabled;

  const Library({
    required this.id,
    required this.name,
    required this.path,
    this.type = 'movie',
    this.enabled = true,
  });

  factory Library.fromJson(Map<String, dynamic> json) {
    return Library(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      path: json['path'] as String? ?? '',
      type: json['type'] as String? ?? 'movie',
      enabled: json['enabled'] as bool? ?? true,
    );
  }
}
