import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/providers.dart';
import '../../theme.dart';
import 'queue_screen.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final health = ref.watch(healthProvider).value;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          _sectionTitle('Server'),
          _Card(
            child: Column(
              children: [
                _Row(
                  icon: Icons.dns_outlined,
                  title: 'Server',
                  subtitle: settings.serverUrl ?? 'Not connected',
                  onTap: () => ref.read(settingsProvider.notifier).clearServer(),
                  trailing: Icon(
                    health != null && health.isOk ? Icons.check_circle : Icons.error_outline,
                    color: health != null && health.isOk ? AppColors.success : AppColors.danger,
                    size: 20,
                  ),
                ),
                _divider(),
                _Row(
                  icon: Icons.info_outline,
                  title: 'Server version',
                  subtitle: health?.version ?? 'Unknown',
                  onTap: null,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          _sectionTitle('Playback'),
          _Card(
            child: Column(
              children: [
                SwitchListTile(
                  dense: true,
                  activeThumbColor: AppColors.accent,
                  title: const Text('Allow 4K streaming', style: TextStyle(color: AppColors.text, fontSize: 14.5)),
                  subtitle: const Text('Play high-resolution content up to 2160p when available', style: TextStyle(color: AppColors.textFaint, fontSize: 12)),
                  value: settings.allow4k,
                  onChanged: (v) => ref.read(settingsProvider.notifier).setAllow4k(v),
                ),
                _divider(),
                SwitchListTile(
                  dense: true,
                  activeThumbColor: AppColors.accent,
                  title: const Text('Play over cellular data', style: TextStyle(color: AppColors.text, fontSize: 14.5)),
                  subtitle: const Text('Allow streaming when not on Wi-Fi', style: TextStyle(color: AppColors.textFaint, fontSize: 12)),
                  value: settings.cellularEnabled,
                  onChanged: (v) => ref.read(settingsProvider.notifier).setCellularEnabled(v),
                ),
                _divider(),
                SwitchListTile(
                  dense: true,
                  activeThumbColor: AppColors.accent,
                  title: const Text('Auto-resume playback', style: TextStyle(color: AppColors.text, fontSize: 14.5)),
                  subtitle: const Text('Continue from where you left off', style: TextStyle(color: AppColors.textFaint, fontSize: 12)),
                  value: settings.autoResume,
                  onChanged: (v) => ref.read(settingsProvider.notifier).setAutoResume(v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          _sectionTitle('Library'),
          _Card(
            child: Column(
              children: [
                _Row(
                  icon: Icons.all_inbox_outlined,
                  title: 'Optimization queue',
                  subtitle: 'View and manage transcode jobs',
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const QueueScreen()),
                  ),
                ),
                _divider(),
                _Row(
                  icon: Icons.sync_outlined,
                  title: 'Scan all libraries',
                  subtitle: 'Detect new and removed media',
                  onTap: () {
                    final api = ref.read(apiClientProvider);
                    if (api == null) return;
                    api.scanAll();
                    ScaffoldMessenger.of(context)
                      ..clearSnackBars()
                      ..showSnackBar(const SnackBar(content: Text('Scan started')));
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 28),
          const Center(
            child: Text(
              'Quark Player  ·  v0.1.0',
              style: TextStyle(color: AppColors.textFaint, fontSize: 12),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _divider() => const Divider(height: 1, indent: 52);

  Widget _sectionTitle(String title) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
        child: Text(
          title,
          style: const TextStyle(
            color: AppColors.accentBright,
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.6,
          ),
        ),
      );
}

class _Card extends StatelessWidget {
  final Widget child;
  const _Card({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: child,
    );
  }
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;
  final Widget? trailing;

  const _Row({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.onTap,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      dense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      leading: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: AppColors.elevated,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: AppColors.accentBright, size: 18),
      ),
      title: Text(title, style: const TextStyle(color: AppColors.text, fontSize: 14, fontWeight: FontWeight.w600)),
      subtitle: Text(
        subtitle,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(color: AppColors.textFaint, fontSize: 12),
      ),
      trailing: trailing ?? const Icon(Icons.chevron_right_rounded, color: AppColors.textFaint, size: 22),
    );
  }
}
