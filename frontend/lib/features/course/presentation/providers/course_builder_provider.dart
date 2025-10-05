import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/course.dart';
import '../../../../shared/models/place.dart';

part 'course_builder_provider.freezed.dart';

@freezed
class CourseBuilderState with _$CourseBuilderState {
  const factory CourseBuilderState({
    required String title,
    required CourseType type,
    required List<CoursePlace> places,
    required Duration totalDuration,
    @Default(false) bool isSaving,
    String? error,
  }) = _CourseBuilderState;

  factory CourseBuilderState.initial() => const CourseBuilderState(
        title: '',
        type: CourseType.date,
        places: [],
        totalDuration: Duration.zero,
      );
}

class CourseBuilderNotifier extends StateNotifier<CourseBuilderState> {
  CourseBuilderNotifier() : super(CourseBuilderState.initial());

  void setTitle(String title) {
    state = state.copyWith(title: title);
  }

  void setType(CourseType type) {
    state = state.copyWith(type: type);
  }

  void addPlace(Place place) {
    final newPlace = CoursePlace(
      id: place.id,
      place: place,
      order: state.places.length + 1,
      startTime: _calculateStartTime(),
      duration: const Duration(hours: 1),
    );

    state = state.copyWith(
      places: [...state.places, newPlace],
    );

    _recalculateRoute();
  }

  void removePlace(int index) {
    final updatedPlaces = List<CoursePlace>.from(state.places);
    updatedPlaces.removeAt(index);

    // Update order numbers
    for (int i = 0; i < updatedPlaces.length; i++) {
      updatedPlaces[i] = updatedPlaces[i].copyWith(order: i + 1);
    }

    state = state.copyWith(places: updatedPlaces);
    _recalculateRoute();
  }

  void reorderPlaces(int oldIndex, int newIndex) {
    if (oldIndex < newIndex) {
      newIndex -= 1;
    }

    final updatedPlaces = List<CoursePlace>.from(state.places);
    final place = updatedPlaces.removeAt(oldIndex);
    updatedPlaces.insert(newIndex, place);

    // Update order numbers
    for (int i = 0; i < updatedPlaces.length; i++) {
      updatedPlaces[i] = updatedPlaces[i].copyWith(order: i + 1);
    }

    state = state.copyWith(places: updatedPlaces);
    _recalculateRoute();
  }

  void updateDuration(int index, Duration duration) {
    final updatedPlaces = List<CoursePlace>.from(state.places);
    updatedPlaces[index] = updatedPlaces[index].copyWith(duration: duration);

    // Recalculate start times for subsequent places
    for (int i = index + 1; i < updatedPlaces.length; i++) {
      final prevPlace = updatedPlaces[i - 1];
      final newStartTime = prevPlace.startTime.add(prevPlace.duration);
      updatedPlaces[i] = updatedPlaces[i].copyWith(startTime: newStartTime);
    }

    state = state.copyWith(places: updatedPlaces);
    _recalculateRoute();
  }

  DateTime _calculateStartTime() {
    if (state.places.isEmpty) {
      return DateTime.now().copyWith(hour: 10, minute: 0, second: 0);
    }

    final lastPlace = state.places.last;
    return lastPlace.startTime.add(lastPlace.duration);
  }

  void _recalculateRoute() {
    // Calculate total duration
    final totalDuration = state.places.fold<Duration>(
      Duration.zero,
      (sum, place) => sum + place.duration,
    );

    state = state.copyWith(totalDuration: totalDuration);
  }

  Future<void> saveCourse() async {
    state = state.copyWith(isSaving: true, error: null);

    try {
      // TODO: Implement API call to save course
      await Future.delayed(const Duration(seconds: 1)); // Simulate API call

      // Success - navigate back or show success message
      state = state.copyWith(isSaving: false);
    } catch (e) {
      state = state.copyWith(
        isSaving: false,
        error: e.toString(),
      );
    }
  }
}

final courseBuilderProvider = StateNotifierProvider.autoDispose<
    CourseBuilderNotifier, CourseBuilderState>((ref) {
  return CourseBuilderNotifier();
});
