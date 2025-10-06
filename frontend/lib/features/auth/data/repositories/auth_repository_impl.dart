import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../../../../core/auth/supabase_service.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../shared/models/user.dart';
import '../../domain/repositories/auth_repository.dart';

/// Auth Repository Implementation
class AuthRepositoryImpl implements AuthRepository {
  final SupabaseClient _supabase;

  AuthRepositoryImpl(this._supabase);

  @override
  User? get currentUser {
    final supabaseUser = _supabase.auth.currentUser;
    if (supabaseUser == null) return null;
    return User.fromSupabase(supabaseUser);
  }

  @override
  Stream<User?> get authStateChanges {
    return _supabase.auth.onAuthStateChange.map((event) {
      final user = event.session?.user;
      if (user == null) return null;
      return User.fromSupabase(user);
    });
  }

  @override
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _supabase.auth.signInWithPassword(
        email: email,
        password: password,
      );

      if (response.user == null) {
        return Left(ApiException(
          message: '로그인에 실패했습니다',
          statusCode: 401,
        ));
      }

      return Right(User.fromSupabase(response.user!));
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: _getStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(
        message: '알 수 없는 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  }) async {
    try {
      final response = await _supabase.auth.signUp(
        email: email,
        password: password,
        data: {
          'name': name,
        },
      );

      if (response.user == null) {
        return Left(ApiException(
          message: '회원가입에 실패했습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromSupabase(response.user!));
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: _getStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(
        message: '알 수 없는 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithGoogle() async {
    try {
      final redirectUrl = dotenv.env['REDIRECT_URL'] ?? 'com.example.hotly://login-callback';

      final response = await _supabase.auth.signInWithOAuth(
        OAuthProvider.google,
        redirectTo: redirectUrl,
      );

      if (!response) {
        return Left(ApiException(
          message: 'Google 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      // OAuth는 비동기로 처리되므로 authStateChanges에서 감지
      return Right(currentUser ?? User.initial());
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: 500,
      ));
    } catch (e) {
      return Left(ApiException(
        message: '알 수 없는 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithApple() async {
    try {
      final redirectUrl = dotenv.env['REDIRECT_URL'] ?? 'com.example.hotly://login-callback';

      final response = await _supabase.auth.signInWithOAuth(
        OAuthProvider.apple,
        redirectTo: redirectUrl,
      );

      if (!response) {
        return Left(ApiException(
          message: 'Apple 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(currentUser ?? User.initial());
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: 500,
      ));
    } catch (e) {
      return Left(ApiException(
        message: '알 수 없는 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> signOut() async {
    try {
      await _supabase.auth.signOut();
      return const Right(null);
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: 500,
      ));
    } catch (e) {
      return Left(ApiException(
        message: '로그아웃에 실패했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> resetPassword(String email) async {
    try {
      final redirectUrl = dotenv.env['REDIRECT_URL'] ?? 'com.example.hotly://reset-password';

      await _supabase.auth.resetPasswordForEmail(
        email,
        redirectTo: redirectUrl,
      );
      return const Right(null);
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: 400,
      ));
    } catch (e) {
      return Left(ApiException(
        message: '비밀번호 재설정 이메일 전송에 실패했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  String _getErrorMessage(AuthException e) {
    final message = e.message.toLowerCase();

    if (message.contains('invalid login credentials') ||
        message.contains('invalid credentials')) {
      return '이메일 또는 비밀번호가 올바르지 않습니다';
    } else if (message.contains('email not confirmed')) {
      return '이메일 인증이 필요합니다';
    } else if (message.contains('user already registered') ||
               message.contains('already registered')) {
      return '이미 가입된 이메일입니다';
    } else if (message.contains('password')) {
      return '비밀번호는 최소 6자 이상이어야 합니다';
    }

    return e.message;
  }

  int _getStatusCode(AuthException e) {
    if (e.statusCode != null) {
      return int.tryParse(e.statusCode!) ?? 500;
    }
    return 500;
  }
}

/// Auth Repository Provider
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final supabase = ref.watch(supabaseClientProvider);
  return AuthRepositoryImpl(supabase);
});
