import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/user.dart';
import '../../../../core/storage/local_storage.dart';

part 'profile_provider.freezed.dart';

@freezed
class ProfileState with _$ProfileState {
  const factory ProfileState({
    User? user,
    UserStats? stats,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingStats,
    String? error,
  }) = _ProfileState;
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  final LocalStorage _localStorage;

  ProfileNotifier(this._localStorage) : super(const ProfileState()) {
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    state = state.copyWith(isLoading: true);

    // TODO: API 연동 시 실제 사용자 정보 로드
    // For now, use mock data
    await Future.delayed(const Duration(milliseconds: 500));

    final mockUser = User(
      id: 'user_001',
      name: '김민지',
      email: 'user@hotly.app',
      profileImageUrl: null,
      savedPlacesCount: 24,
      likedPlacesCount: 48,
      coursesCount: 6,
      createdAt: DateTime.now().subtract(const Duration(days: 30)),
    );

    final mockStats = const UserStats(
      savedPlaces: 24,
      likedPlaces: 48,
      courses: 6,
    );

    state = state.copyWith(
      isLoading: false,
      user: mockUser,
      stats: mockStats,
    );
  }

  Future<void> refresh() async {
    await _loadUserProfile();
  }

  Future<void> logout() async {
    await _localStorage.clearAll();
    state = ProfileState(
      user: User.initial(),
      stats: const UserStats(),
    );
  }
}

final profileProvider =
    StateNotifierProvider<ProfileNotifier, ProfileState>((ref) {
  final localStorage = ref.watch(localStorageProvider);
  return ProfileNotifier(localStorage);
});
