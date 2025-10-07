import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/storage/local_storage.dart';

part 'onboarding_provider.freezed.dart';

@freezed
class OnboardingState with _$OnboardingState {
  const factory OnboardingState({
    @Default(0) int currentStep,
    @Default([]) List<String> selectedInterests,
    @Default([]) List<String> selectedCategories,
    @Default(false) bool locationPermissionGranted,
    @Default(false) bool notificationPermissionGranted,
    @Default(false) bool isCompleted,
  }) = _OnboardingState;
}

class OnboardingNotifier extends StateNotifier<OnboardingState> {
  final LocalStorage _localStorage;

  OnboardingNotifier(this._localStorage) : super(const OnboardingState());

  void nextStep() {
    if (state.currentStep < 3) {
      state = state.copyWith(currentStep: state.currentStep + 1);
    }
  }

  void previousStep() {
    if (state.currentStep > 0) {
      state = state.copyWith(currentStep: state.currentStep - 1);
    }
  }

  void goToStep(int step) {
    state = state.copyWith(currentStep: step);
  }

  void toggleInterest(String interest) {
    final interests = List<String>.from(state.selectedInterests);
    if (interests.contains(interest)) {
      interests.remove(interest);
    } else {
      interests.add(interest);
    }
    state = state.copyWith(selectedInterests: interests);
  }

  void toggleCategory(String category) {
    final categories = List<String>.from(state.selectedCategories);
    if (categories.contains(category)) {
      categories.remove(category);
    } else {
      categories.add(category);
    }
    state = state.copyWith(selectedCategories: categories);
  }

  void setLocationPermission(bool granted) {
    state = state.copyWith(locationPermissionGranted: granted);
  }

  void setNotificationPermission(bool granted) {
    state = state.copyWith(notificationPermissionGranted: granted);
  }

  Future<void> completeOnboarding() async {
    await _localStorage.setOnboardingCompleted(true);
    state = state.copyWith(isCompleted: true);
  }

  void skipOnboarding() {
    _localStorage.setOnboardingCompleted(true);
    state = state.copyWith(isCompleted: true);
  }
}

final onboardingProvider =
    StateNotifierProvider<OnboardingNotifier, OnboardingState>((ref) {
  final localStorage = ref.watch(localStorageProvider);
  return OnboardingNotifier(localStorage);
});

/// 온보딩 완료 여부 확인
final isOnboardingCompletedProvider = Provider<bool>((ref) {
  // OnboardingNotifier의 isCompleted 상태를 watch
  final onboardingState = ref.watch(onboardingProvider);
  if (onboardingState.isCompleted) {
    return true;
  }

  // 앱 시작 시 LocalStorage에서 초기값 확인
  final localStorage = ref.watch(localStorageProvider);
  return localStorage.isOnboardingCompleted;
});
