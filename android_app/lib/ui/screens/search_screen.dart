import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../models/query.dart';
import '../../providers/providers.dart';
import '../../theme.dart';
import '../navigation.dart';
import '../widgets/empty_state.dart';
import '../widgets/poster_card.dart';
import '../widgets/shimmer.dart';
import '../widgets/state_views.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _controller = TextEditingController();
  Timer? _debounce;
  String _query = '';
  String _genre = '';
  bool _unwatched = false;
  String _sort = 'recently_added';

  Future<QueryResult>? _result;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), () {
      setState(() => _query = value.trim());
    });
  }

  void _run() {
    setState(() {
      _result = _fetch();
    });
  }

  Future<QueryResult> _fetch() {
    final api = ref.read(apiClientProvider);
    if (api == null) throw const ApiException('No server configured');
    final q = _query.isEmpty ? '' : _query;
    return api.queryItems(
      ItemQuery(
        search: q.isEmpty ? null : q,
        genres: _genre.isEmpty ? const [] : [_genre],
        unwatched: _unwatched ? true : null,
        sort: _sort,
        limit: 200,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final genresAsync = ref.watch(genresProvider);
    final genres = genresAsync.value ?? const <String>[];

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 8,
        title: TextField(
          controller: _controller,
          onChanged: _onChanged,
          textInputAction: TextInputAction.search,
          style: const TextStyle(color: AppColors.text, fontSize: 15),
          decoration: InputDecoration(
            hintText: 'Search movies & shows',
            prefixIcon: const Icon(Icons.search_rounded, color: AppColors.textFaint, size: 20),
            suffixIcon: _controller.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.close, color: AppColors.textFaint, size: 18),
                    onPressed: () {
                      _controller.clear();
                      _onChanged('');
                      setState(() => _result = null);
                    },
                  )
                : null,
          ),
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _genre.isEmpty ? null : _genre,
                    isExpanded: true,
                    hint: const Text('All genres', style: TextStyle(color: AppColors.textFaint, fontSize: 13)),
                    items: [
                      for (final g in genres)
                        DropdownMenuItem(value: g, child: Text(g, style: const TextStyle(fontSize: 13))),
                    ],
                    onChanged: (v) => setState(() {
                      _genre = v ?? '';
                      _run();
                    }),
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      filled: true,
                      fillColor: AppColors.surface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: AppColors.border),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _sort,
                    isExpanded: true,
                    items: const [
                      DropdownMenuItem(value: 'recently_added', child: Text('Recently added', style: TextStyle(fontSize: 13))),
                      DropdownMenuItem(value: 'rating', child: Text('Highest rated', style: TextStyle(fontSize: 13))),
                      DropdownMenuItem(value: 'title', child: Text('Title A–Z', style: TextStyle(fontSize: 13))),
                      DropdownMenuItem(value: 'year', child: Text('Newest first', style: TextStyle(fontSize: 13))),
                    ],
                    onChanged: (v) => setState(() {
                      _sort = v ?? 'recently_added';
                      _run();
                    }),
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      filled: true,
                      fillColor: AppColors.surface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: AppColors.border),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () => setState(() {
                    _unwatched = !_unwatched;
                    _run();
                  }),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    decoration: BoxDecoration(
                      color: _unwatched ? AppColors.accent.withValues(alpha: 0.22) : AppColors.surface,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: _unwatched ? AppColors.accent : AppColors.border,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _unwatched ? Icons.done_all_rounded : Icons.done_all_outlined,
                          color: _unwatched ? AppColors.accentBright : AppColors.textFaint,
                          size: 16,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Unwatched',
                          style: TextStyle(
                            color: _unwatched ? AppColors.accentBright : AppColors.textFaint,
                            fontSize: 11.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _buildBody(),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    final future = _result;
    final hasQuery = _query.isNotEmpty || _genre.isNotEmpty || _unwatched;
    if (future == null && !hasQuery) {
      return const EmptyState(
        icon: Icons.search_rounded,
        title: 'Search your library',
        subtitle: 'Find movies and shows by title, genre, or status.',
      );
    }
    return FutureBuilder<QueryResult>(
      future: future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const PosterGridSkeleton();
        }
        if (snap.hasError) {
          return ErrorView(
            message: snap.error.toString(),
            onRetry: () => setState(() => _result = _fetch()),
          );
        }
        final qr = snap.data;
        if (qr == null || qr.items.isEmpty) {
          return const EmptyState(
            icon: Icons.search_off_rounded,
            title: 'No results',
            subtitle: 'Try a different search or clear some filters.',
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            final f = _fetch();
            setState(() => _result = f);
            await f;
          },
          color: AppColors.accent,
          child: GridView.builder(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
            physics: const AlwaysScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 10,
              mainAxisSpacing: 12,
              childAspectRatio: 0.52,
            ),
            itemCount: qr.items.length,
            itemBuilder: (context, i) {
              final item = qr.items[i];
              return PosterCard(
                item: item,
                heroTag: 'poster-${item.mediaId}',
                onTap: () => openItem(context, item),
              );
            },
          ),
        );
      },
    );
  }
}
