import 'package:dartz/dartz.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../shared/models/user.dart';

/// Auth Repository Interface
abstract class AuthRepository {
  /// 현재 로그인된 사용자 조회
  User? get currentUser;

  /// 인증 상태 스트림
  Stream<User?> get authStateChanges;

  /// 이메일/비밀번호 로그인
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  });

  /// 이메일/비밀번호 회원가입
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  });

  /// Google OAuth 로그인
  Future<Either<ApiException, User>> signInWithGoogle();

  /// Apple OAuth 로그인
  Future<Either<ApiException, User>> signInWithApple();

  /// 로그아웃
  Future<Either<ApiException, void>> signOut();

  /// 비밀번호 재설정 이메일 전송
  Future<Either<ApiException, void>> resetPassword(String email);
}
