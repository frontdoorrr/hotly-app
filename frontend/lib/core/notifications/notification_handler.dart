import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';

/// Notification Deep Link Handler
class NotificationHandler {
  static final Logger _logger = Logger();

  /// Handle notification tap and navigate to appropriate screen
  static void handleNotificationTap(
    BuildContext context,
    Map<String, dynamic> data,
  ) {
    _logger.i('Handling notification tap: $data');

    final type = data['type'] as String?;
    final id = data['id'] as String?;

    if (type == null) {
      _logger.w('Notification type is null, ignoring');
      return;
    }

    switch (type) {
      case 'place':
        if (id != null) {
          context.push('/places/$id');
        }
        break;

      case 'course':
        if (id != null) {
          context.push('/courses/$id/edit');
        }
        break;

      case 'recommendation':
        // Navigate to home with specific tab or filter
        context.go('/');
        break;

      case 'nearby':
        // Navigate to map with location
        final lat = double.tryParse(data['lat'] as String? ?? '');
        final lng = double.tryParse(data['lng'] as String? ?? '');
        if (lat != null && lng != null) {
          context.push('/map');
          // TODO: Set map center to lat, lng
        }
        break;

      case 'search':
        final query = data['query'] as String?;
        if (query != null) {
          context.push('/search');
          // TODO: Set search query
        }
        break;

      case 'profile':
        context.push('/profile');
        break;

      default:
        _logger.w('Unknown notification type: $type');
        context.go('/');
    }
  }

  /// Get notification route from payload
  static String? getRouteFromPayload(Map<String, dynamic> data) {
    final type = data['type'] as String?;
    final id = data['id'] as String?;

    if (type == null) return null;

    switch (type) {
      case 'place':
        return id != null ? '/places/$id' : null;
      case 'course':
        return id != null ? '/courses/$id/edit' : null;
      case 'map':
        return '/map';
      case 'search':
        return '/search';
      case 'profile':
        return '/profile';
      default:
        return '/';
    }
  }
}
