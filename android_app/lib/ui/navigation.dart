import 'package:flutter/material.dart';

import '../models/item.dart';
import 'screens/item_detail_screen.dart';
import 'screens/player_screen.dart';
import 'screens/show_detail_screen.dart';

void openItem(BuildContext context, Item item) {
  if (item.isEpisode && item.seriesTitle != null && item.seriesTitle!.isNotEmpty) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ShowDetailScreen(seriesTitle: item.seriesTitle!)),
    );
  } else {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ItemDetailScreen(mediaId: item.mediaId)),
    );
  }
}

void playItem(
  BuildContext context, {
  required String mediaId,
  required String title,
  double initialPosition = 0,
}) {
  Navigator.of(context).push(
    MaterialPageRoute(
      builder: (_) => PlayerScreen(
        mediaId: mediaId,
        title: title,
        initialPosition: initialPosition,
      ),
    ),
  );
}
