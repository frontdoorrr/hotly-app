import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/models/place.dart';

class RouteInfoCard extends StatelessWidget {
  final CoursePlace from;
  final CoursePlace to;

  const RouteInfoCard({
    super.key,
    required this.from,
    required this.to,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // TODO: Calculate actual route info from API
    final transportMode = _getTransportMode();
    final duration = _calculateDuration();
    final distance = _calculateDistance();

    return Container(
      margin: const EdgeInsets.symmetric(
        horizontal: AppTheme.space4,
        vertical: AppTheme.space1,
      ),
      padding: const EdgeInsets.symmetric(
        horizontal: AppTheme.space4,
        vertical: AppTheme.space2,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            transportMode == 'walk' ? Icons.directions_walk : Icons.directions_car,
            size: 16,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: AppTheme.space2),
          Text(
            '$transportMode $duration, $distance',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.primary,
            ),
          ),
          const Icon(
            Icons.arrow_downward,
            size: 16,
            color: Colors.grey,
          ),
        ],
      ),
    );
  }

  String _getTransportMode() {
    // TODO: Implement actual logic based on distance
    final dist = _calculateDistanceInMeters();
    return dist < 1000 ? '도보' : '차량';
  }

  String _calculateDuration() {
    // TODO: Implement actual API call for route calculation
    return '10분';
  }

  String _calculateDistance() {
    // TODO: Implement actual distance calculation
    final dist = _calculateDistanceInMeters();
    if (dist < 1000) {
      return '${dist}m';
    } else {
      return '${(dist / 1000).toStringAsFixed(1)}km';
    }
  }

  double _calculateDistanceInMeters() {
    // Simple Euclidean distance for now
    // TODO: Use proper Haversine formula or API

    // Handle null coordinates
    if (to.place.longitude == null || from.place.longitude == null ||
        to.place.latitude == null || from.place.latitude == null) {
      return 0.0;
    }

    const double metersPerDegree = 111000;
    final dx = (to.place.longitude! - from.place.longitude!) * metersPerDegree;
    final dy = (to.place.latitude! - from.place.latitude!) * metersPerDegree;
    return (dx * dx + dy * dy) / metersPerDegree;
  }
}
