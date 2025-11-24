import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/sharing/share_service.dart';
import '../../../../shared/models/course.dart';
import '../../../../shared/widgets/atoms/app_button.dart';
import '../../../../shared/widgets/atoms/app_input.dart';
import '../providers/course_builder_provider.dart';
import '../widgets/course_place_card.dart';
import '../widgets/route_info_card.dart';

class CourseBuilderScreen extends ConsumerStatefulWidget {
  final String? courseId;

  const CourseBuilderScreen({
    super.key,
    this.courseId,
  });

  @override
  ConsumerState<CourseBuilderScreen> createState() =>
      _CourseBuilderScreenState();
}

class _CourseBuilderScreenState extends ConsumerState<CourseBuilderScreen> {
  final _titleController = TextEditingController();

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(courseBuilderProvider);
    final notifier = ref.read(courseBuilderProvider.notifier);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.profile_createCourse),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: state.places.isEmpty
                ? null
                : () async {
                    await ShareService.shareCourse(
                      courseId: widget.courseId ?? 'new',
                      courseName: state.title ?? context.l10n.course_newCourse,
                      placeCount: state.places.length,
                      duration: _formatDuration(state.totalDuration),
                    );
                  },
          ),
          TextButton(
            onPressed: () {
              // TODO: Navigate to preview
            },
            child: Text(context.l10n.common_preview),
          ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          // Course Info Section
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.space4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title Input
                  AppInput(
                    label: context.l10n.course_title,
                    placeholder: context.l10n.course_titleHint,
                    controller: _titleController,
                    onChanged: notifier.setTitle,
                    isRequired: true,
                  ),
                  const SizedBox(height: AppTheme.space4),

                  // Course Type Chips
                  Text(
                    context.l10n.course_type,
                    style: theme.textTheme.labelMedium,
                  ),
                  const SizedBox(height: AppTheme.space2),
                  Wrap(
                    spacing: AppTheme.space2,
                    children: [
                      _buildTypeChip(
                        context,
                        context.l10n.course_date,
                        CourseType.date,
                        state.type,
                        notifier.setType,
                      ),
                      _buildTypeChip(
                        context,
                        context.l10n.course_travel,
                        CourseType.travel,
                        state.type,
                        notifier.setType,
                      ),
                      _buildTypeChip(
                        context,
                        context.l10n.course_foodTour,
                        CourseType.foodTour,
                        state.type,
                        notifier.setType,
                      ),
                      _buildTypeChip(
                        context,
                        context.l10n.course_other,
                        CourseType.other,
                        state.type,
                        notifier.setType,
                      ),
                    ],
                  ),
                  const SizedBox(height: AppTheme.space4),
                  const Divider(),
                ],
              ),
            ),
          ),

          // Timeline Header
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppTheme.space4,
                vertical: AppTheme.space2,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${context.l10n.course_places} (${state.places.length})',
                    style: theme.textTheme.labelLarge,
                  ),
                  Text(
                    '${context.l10n.course_totalDuration} ${_formatDuration(state.totalDuration)}',
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Places List with Drag & Drop
          if (state.places.isEmpty)
            SliverToBoxAdapter(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(AppTheme.space8),
                  child: Column(
                    children: [
                      Icon(
                        Icons.add_location_alt_outlined,
                        size: 64,
                        color: Colors.grey.shade400,
                      ),
                      const SizedBox(height: AppTheme.space4),
                      Text(
                        context.l10n.course_addPlacePrompt,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            )
          else
            SliverReorderableList(
              itemCount: state.places.length * 2 - 1,
              onReorder: (oldIndex, newIndex) {
                // Only reorder place items (even indices)
                if (oldIndex.isEven && newIndex.isEven) {
                  HapticFeedback.mediumImpact();
                  notifier.reorderPlaces(oldIndex ~/ 2, newIndex ~/ 2);
                }
              },
              itemBuilder: (context, index) {
                if (index.isOdd) {
                  // Route Info Card (non-draggable)
                  final placeIndex = index ~/ 2;
                  return RouteInfoCard(
                    key: ValueKey('route_$placeIndex'),
                    from: state.places[placeIndex],
                    to: state.places[placeIndex + 1],
                  );
                }

                // Place Card (draggable)
                final placeIndex = index ~/ 2;
                final place = state.places[placeIndex];

                return CoursePlaceCard(
                  key: ValueKey('place_${place.id}'),
                  place: place,
                  order: placeIndex + 1,
                  onDurationChanged: (duration) {
                    notifier.updateDuration(placeIndex, duration);
                  },
                  onDelete: () {
                    notifier.removePlace(placeIndex);
                  },
                );
              },
            ),

          // Add Place Button
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.space4),
              child: OutlinedButton.icon(
                onPressed: () {
                  // TODO: Navigate to place search/selection
                  _showAddPlaceDialog(context);
                },
                icon: const Icon(Icons.add),
                label: Text(context.l10n.course_addPlace),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                ),
              ),
            ),
          ),

          // Bottom Padding
          const SliverToBoxAdapter(
            child: SizedBox(height: 80),
          ),
        ],
      ),

      // Bottom Action Bar
      bottomNavigationBar: BottomAppBar(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppTheme.space4,
            vertical: AppTheme.space2,
          ),
          child: Row(
            children: [
              Expanded(
                child: AppButton(
                  text: context.l10n.common_cancel,
                  variant: ButtonVariant.outline,
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
              const SizedBox(width: AppTheme.space4),
              Expanded(
                flex: 2,
                child: AppButton(
                  text: context.l10n.common_save,
                  isLoading: state.isSaving,
                  isDisabled: state.title.isEmpty || state.places.isEmpty,
                  onPressed: () async {
                    await notifier.saveCourse();
                    if (!mounted) return;

                    if (state.error == null) {
                      Navigator.of(context).pop();
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(state.error!)),
                      );
                    }
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTypeChip(
    BuildContext context,
    String label,
    CourseType type,
    CourseType selectedType,
    Function(CourseType) onSelected,
  ) {
    final theme = Theme.of(context);
    final isSelected = type == selectedType;

    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => onSelected(type),
      selectedColor: theme.colorScheme.primary,
      labelStyle: TextStyle(
        color: isSelected ? Colors.white : theme.colorScheme.onSurface,
      ),
    );
  }

  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);

    if (hours > 0 && minutes > 0) {
      return '$hours${context.l10n.course_hour} $minutes${context.l10n.course_minute}';
    } else if (hours > 0) {
      return '$hours${context.l10n.course_hour}';
    } else if (minutes > 0) {
      return '$minutes${context.l10n.course_minute}';
    } else {
      return '0${context.l10n.course_minute}';
    }
  }

  void _showAddPlaceDialog(BuildContext context) {
    // TODO: Implement proper place selection flow
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(context.l10n.course_searchInDevelopment),
      ),
    );
  }
}
