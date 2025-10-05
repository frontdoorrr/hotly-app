import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/models/place.dart';

class CoursePlaceCard extends StatefulWidget {
  final CoursePlace place;
  final int order;
  final Function(Duration) onDurationChanged;
  final VoidCallback onDelete;

  const CoursePlaceCard({
    super.key,
    required this.place,
    required this.order,
    required this.onDurationChanged,
    required this.onDelete,
  });

  @override
  State<CoursePlaceCard> createState() => _CoursePlaceCardState();
}

class _CoursePlaceCardState extends State<CoursePlaceCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final endTime = widget.place.startTime.add(widget.place.duration);

    return Card(
      margin: const EdgeInsets.symmetric(
        horizontal: AppTheme.space4,
        vertical: AppTheme.space2,
      ),
      child: Column(
        children: [
          ListTile(
            leading: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.drag_handle,
                  color: Colors.grey,
                ),
                const SizedBox(width: AppTheme.space2),
                CircleAvatar(
                  radius: 16,
                  backgroundColor: theme.colorScheme.primary,
                  child: Text(
                    '${widget.order}',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            title: Text(
              widget.place.place.name,
              style: theme.textTheme.labelLarge,
            ),
            subtitle: Text(
              '${_formatTime(widget.place.startTime)} - '
              '${_formatTime(endTime)} '
              '(${widget.place.duration.inMinutes}분)',
              style: theme.textTheme.bodySmall,
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: Icon(
                    _isExpanded ? Icons.expand_less : Icons.expand_more,
                  ),
                  onPressed: () {
                    setState(() => _isExpanded = !_isExpanded);
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: widget.onDelete,
                  color: theme.colorScheme.error,
                ),
              ],
            ),
          ),

          // Duration adjustment slider (shown when expanded)
          if (_isExpanded)
            Padding(
              padding: const EdgeInsets.all(AppTheme.space4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '체류 시간',
                    style: theme.textTheme.labelMedium,
                  ),
                  const SizedBox(height: AppTheme.space2),
                  Slider(
                    value: widget.place.duration.inMinutes.toDouble(),
                    min: 30,
                    max: 240,
                    divisions: 14,
                    label: '${widget.place.duration.inMinutes}분',
                    onChanged: (value) {
                      widget.onDurationChanged(
                        Duration(minutes: value.toInt()),
                      );
                    },
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '30분',
                        style: theme.textTheme.bodySmall,
                      ),
                      Text(
                        '4시간',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:'
        '${time.minute.toString().padLeft(2, '0')}';
  }
}
