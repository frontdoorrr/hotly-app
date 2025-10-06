import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../shared/models/user.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/repositories/auth_repository.dart';

part 'auth_provider.freezed.dart';

enum AuthStatus {
  initial,        // 초기 상태
  authenticated,  // 로그인됨
  unauthenticated, // 로그인 안 됨
}

@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    User? user,
    @Default(AuthStatus.initial) AuthStatus status,
    @Default(false) bool isLoading,
    ApiException? error,
  }) = _AuthState;
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;
  StreamSubscription<User?>? _authSubscription;

  AuthNotifier(this._repository) : super(const AuthState()) {
    _checkInitialAuth();
    _listenToAuthChanges();
  }

  Future<void> _checkInitialAuth() async {
    final currentUser = _repository.currentUser;
    state = state.copyWith(
      user: currentUser,
      status: currentUser != null
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated,
    );
  }

  void _listenToAuthChanges() {
    _authSubscription = _repository.authStateChanges.listen((user) {
      state = state.copyWith(
        user: user,
        status: user != null
            ? AuthStatus.authenticated
            : AuthStatus.unauthenticated,
      );
    });
  }

  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.signInWithEmail(
      email: email,
      password: password,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
          status: AuthStatus.unauthenticated,
        );
      },
      (user) {
        state = state.copyWith(
          isLoading: false,
          user: user,
          status: AuthStatus.authenticated,
          error: null,
        );
      },
    );
  }

  Future<void> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.signUpWithEmail(
      email: email,
      password: password,
      name: name,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (user) {
        state = state.copyWith(
          isLoading: false,
          user: user,
          status: user.emailConfirmed
              ? AuthStatus.authenticated
              : AuthStatus.unauthenticated,
          error: null,
        );
      },
    );
  }

  Future<void> signInWithGoogle() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.signInWithGoogle();

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (_) {
        // OAuth는 authStateChanges에서 자동으로 상태 업데이트
        state = state.copyWith(isLoading: false);
      },
    );
  }

  Future<void> signInWithApple() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.signInWithApple();

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (_) {
        state = state.copyWith(isLoading: false);
      },
    );
  }

  Future<void> signOut() async {
    await _repository.signOut();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> resetPassword(String email) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.resetPassword(email);

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (_) {
        state = state.copyWith(
          isLoading: false,
          error: null,
        );
      },
    );
  }

  @override
  void dispose() {
    _authSubscription?.cancel();
    super.dispose();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});

/// Helper for checking auth status
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).status == AuthStatus.authenticated;
});
