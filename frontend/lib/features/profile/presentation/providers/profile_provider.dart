import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/user.dart';
import '../../../../core/storage/local_storage.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/repositories/profile_repository_impl.dart';
import '../../domain/repositories/profile_repository.dart';

part 'profile_provider.freezed.dart';

@freezed
class ProfileState with _$ProfileState {
  const factory ProfileState({
    User? user,
    UserStats? stats,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingStats,
    @Default(false) bool isAuthenticated,
    String? error,
  }) = _ProfileState;
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  final LocalStorage _localStorage;
  final ProfileRepository _repository;
  final Ref _ref;

  ProfileNotifier(this._localStorage, this._repository, this._ref)
      : super(const ProfileState()) {
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    state = state.copyWith(isLoading: true);

    // authProvider에서 인증 상태 확인
    final authState = _ref.read(authProvider);

    if (authState.status != AuthStatus.authenticated || authState.user == null) {
      state = state.copyWith(
        isLoading: false,
        user: null,
        stats: null,
        isAuthenticated: false,
      );
      return;
    }

    // 백엔드 API에서 프로필 조회
    final result = await _repository.getProfile();

    result.fold(
      (error) {
        AppLogger.w('Failed to load profile from API: ${error.message}',
            tag: 'Profile');
        // API 실패 시 authProvider의 사용자 정보 사용
        state = state.copyWith(
          isLoading: false,
          user: authState.user,
          stats: const UserStats(savedPlaces: 0, likedPlaces: 0, courses: 0),
          isAuthenticated: true,
        );
      },
      (user) {
        state = state.copyWith(
          isLoading: false,
          user: user,
          stats: const UserStats(savedPlaces: 0, likedPlaces: 0, courses: 0),
          isAuthenticated: true,
        );
      },
    );
  }

  Future<void> refresh() async {
    await _loadUserProfile();
  }

  Future<bool> updateProfile({String? displayName, String? phoneNumber}) async {
    state = state.copyWith(isLoading: true);

    final result = await _repository.updateProfile(
      displayName: displayName,
      phoneNumber: phoneNumber,
    );

    return result.fold(
      (error) {
        AppLogger.e('Failed to update profile: ${error.message}',
            tag: 'Profile');
        state = state.copyWith(isLoading: false, error: error.message);
        return false;
      },
      (user) {
        AppLogger.d('Profile updated successfully', tag: 'Profile');
        state = state.copyWith(isLoading: false, user: user, error: null);
        return true;
      },
    );
  }

  Future<String?> uploadProfileImage(String imagePath) async {
    final result = await _repository.uploadProfileImage(imagePath);

    return result.fold(
      (error) {
        AppLogger.e('Failed to upload image: ${error.message}', tag: 'Profile');
        return null;
      },
      (imageUrl) {
        // 프로필 새로고침
        refresh();
        return imageUrl;
      },
    );
  }

  Future<void> logout() async {
    await _ref.read(authProvider.notifier).signOut();
    await _localStorage.clearAll();

    state = const ProfileState(
      user: null,
      stats: null,
      isAuthenticated: false,
    );
  }
}

final profileProvider =
    StateNotifierProvider<ProfileNotifier, ProfileState>((ref) {
  final localStorage = ref.watch(localStorageProvider);
  final repository = ref.watch(profileRepositoryProvider);

  // authProvider 상태 변경 시 프로필 갱신
  ref.listen(authProvider, (previous, next) {
    if (previous?.status != next.status) {
      ref.invalidateSelf();
    }
  });

  return ProfileNotifier(localStorage, repository, ref);
});
