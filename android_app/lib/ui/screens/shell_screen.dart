import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/providers.dart';
import '../../theme.dart';
import '../widgets/mini_player_bar.dart';
import 'home_screen.dart';
import 'movies_screen.dart';
import 'search_screen.dart';
import 'settings_screen.dart';
import 'shows_screen.dart';

class ShellScreen extends ConsumerWidget {
  const ShellScreen({super.key});

  static const _tabs = [
    _Tab(icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Home'),
    _Tab(icon: Icons.movie_outlined, activeIcon: Icons.movie_rounded, label: 'Movies'),
    _Tab(icon: Icons.live_tv_outlined, activeIcon: Icons.live_tv_rounded, label: 'Shows'),
    _Tab(icon: Icons.search_outlined, activeIcon: Icons.search_rounded, label: 'Search'),
    _Tab(icon: Icons.settings_outlined, activeIcon: Icons.settings_rounded, label: 'Settings'),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(wsEventsProvider, (prev, next) {
      next.maybeWhen(
        data: (event) {
          if (event.isOptimizeRelated) {
            ref.invalidate(queueProvider);
            ref.invalidate(itemsProvider);
            ref.invalidate(showsProvider);
          } else if (event.isScanRelated || event.isMetadataRelated) {
            ref.invalidate(itemsProvider);
            ref.invalidate(showsProvider);
            ref.invalidate(recentProvider);
            ref.invalidate(statesProvider);
            ref.invalidate(librariesProvider);
          }
        },
        orElse: () {},
      );
    });

    final index = ref.watch(tabIndexProvider);

    return Scaffold(
      body: IndexedStack(
        index: index,
        children: const [
          HomeScreen(),
          MoviesScreen(),
          ShowsScreen(),
          SearchScreen(),
          SettingsScreen(),
        ],
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const MiniPlayerBar(),
          NavigationBar(
            selectedIndex: index,
            onDestinationSelected: (i) => ref.read(tabIndexProvider.notifier).state = i,
            destinations: [
              for (final tab in _tabs)
                NavigationDestination(
                  icon: Icon(tab.icon),
                  selectedIcon: Icon(tab.activeIcon),
                  label: tab.label,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Tab {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  const _Tab({required this.icon, required this.activeIcon, required this.label});
}

class HealthGate extends ConsumerWidget {
  const HealthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider);
    return health.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator(color: AppColors.accent))),
      error: (e, _) => Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.wifi_off_rounded, color: AppColors.textFaint, size: 48),
                const SizedBox(height: 16),
                const Text(
                  'Server unreachable',
                  style: TextStyle(color: AppColors.text, fontSize: 17, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                Text(
                  e.toString(),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textFaint, fontSize: 13, height: 1.4),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    OutlinedButton(
                      onPressed: () => ref.invalidate(healthProvider),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.accentBright,
                        side: const BorderSide(color: AppColors.border),
                      ),
                      child: const Text('Retry'),
                    ),
                    const SizedBox(width: 12),
                    OutlinedButton(
                      onPressed: () => ref.read(settingsProvider.notifier).clearServer(),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.textDim,
                        side: const BorderSide(color: AppColors.border),
                      ),
                      child: const Text('Change server'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
      data: (_) => const ShellScreen(),
    );
  }
}
