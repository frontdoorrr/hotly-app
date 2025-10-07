import 'package:dartz/dartz.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/user.dart';

/// Auth Repository Interface (Firebase Authentication)
abstract class AuthRepository {
  /// 현재 로그인된 사용자 조회
  User? get currentUser;

  /// 인증 상태 스트림
  Stream<User?> get authStateChanges;

  /// 현재 사용자의 ID Token 가져오기 (API 호출 시 사용)
  Future<Either<ApiException, String>> getIdToken({bool forceRefresh = false});

  /// Email/Password 로그인
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  });

  /// Email/Password 회원가입
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    String? displayName,
  });

  /// Google 소셜 로그인
  Future<Either<ApiException, User>> signInWithGoogle();

  /// Apple 소셜 로그인
  Future<Either<ApiException, User>> signInWithApple();

  /// Kakao 소셜 로그인
  Future<Either<ApiException, User>> signInWithKakao();

  /// 익명 로그인 (게스트 모드)
  Future<Either<ApiException, User>> signInAnonymously();

  /// 익명 사용자를 Google 계정으로 업그레이드
  Future<Either<ApiException, User>> linkWithGoogle();

  /// 익명 사용자를 Apple 계정으로 업그레이드
  Future<Either<ApiException, User>> linkWithApple();

  /// 로그아웃
  Future<Either<ApiException, void>> signOut();

  /// 회원 탈퇴
  Future<Either<ApiException, void>> deleteAccount();

  /// 프로필 업데이트
  Future<Either<ApiException, void>> updateProfile({
    String? displayName,
    String? photoURL,
  });

  /// 익명 사용자 여부 확인
  bool get isAnonymous;
}
