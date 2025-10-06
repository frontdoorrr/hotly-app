import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';
import 'package:uni_links/uni_links.dart';
import 'dart:async';

/// Deep Link Handler for app links and universal links
class DeepLinkHandler {
  static final Logger _logger = Logger();
  static StreamSubscription? _linkSubscription;

  /// Initialize deep link handling
  static Future<void> initialize(GlobalKey<NavigatorState> navigatorKey) async {
    try {
      // Handle initial deep link (app was terminated)
      final initialLink = await getInitialLink();
      if (initialLink != null) {
        _logger.i('Initial deep link: $initialLink');
        _handleDeepLink(initialLink, navigatorKey.currentContext);
      }

      // Listen for deep links while app is running
      _linkSubscription = linkStream.listen(
        (String? link) {
          if (link != null) {
            _logger.i('Deep link received: $link');
            _handleDeepLink(link, navigatorKey.currentContext);
          }
        },
        onError: (err) {
          _logger.e('Deep link error: $err');
        },
      );
    } catch (e) {
      _logger.e('Failed to initialize deep link handler: $e');
    }
  }

  /// Handle deep link navigation
  static void _handleDeepLink(String link, BuildContext? context) {
    if (context == null || !context.mounted) {
      _logger.w('Context not available for deep link');
      return;
    }

    try {
      final uri = Uri.parse(link);
      final path = uri.path;
      final queryParams = uri.queryParameters;

      _logger.i('Deep link path: $path, params: $queryParams');

      // Parse path and navigate
      if (path.startsWith('/place/')) {
        final placeId = path.substring('/place/'.length);
        context.push('/places/$placeId');
      } else if (path.startsWith('/course/')) {
        final courseId = path.substring('/course/'.length);
        context.push('/courses/$courseId/edit');
      } else if (path == '/map') {
        final lat = queryParams['lat'];
        final lng = queryParams['lng'];
        context.push('/map');
        // TODO: Set map center to lat, lng
      } else if (path == '/search') {
        final query = queryParams['q'];
        context.push('/search');
        // TODO: Set search query
      } else {
        _logger.w('Unknown deep link path: $path');
        context.go('/');
      }
    } catch (e) {
      _logger.e('Failed to handle deep link: $e');
      if (context.mounted) {
        context.go('/');
      }
    }
  }

  /// Dispose deep link subscription
  static void dispose() {
    _linkSubscription?.cancel();
    _linkSubscription = null;
  }
}
