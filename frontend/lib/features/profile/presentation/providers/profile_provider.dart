import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/user.dart';
import '../../../../core/storage/local_storage.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

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
  final Ref _ref;

  ProfileNotifier(this._localStorage, this._ref) : super(const ProfileState()) {
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    state = state.copyWith(isLoading: true);

    // authProvider에서 인증 상태 확인
    final authState = _ref.read(authProvider);

    if (authState.status != AuthStatus.authenticated || authState.user == null) {
      // 로그인되지 않음
      state = state.copyWith(
        isLoading: false,
        user: null,
        stats: null,
        isAuthenticated: false,
      );
      return;
    }

    // 로그인된 사용자 정보 사용
    final user = authState.user!;

    // TODO: API에서 추가 사용자 통계 로드
    final stats = const UserStats(
      savedPlaces: 0,
      likedPlaces: 0,
      courses: 0,
    );

    state = state.copyWith(
      isLoading: false,
      user: user,
      stats: stats,
      isAuthenticated: true,
    );
  }

  Future<void> refresh() async {
    await _loadUserProfile();
  }

  Future<void> logout() async {
    // authProvider의 signOut 호출
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

  // authProvider 상태 변경 시 프로필 갱신
  ref.listen(authProvider, (previous, next) {
    if (previous?.status != next.status) {
      ref.invalidateSelf();
    }
  });

  return ProfileNotifier(localStorage, ref);
});
