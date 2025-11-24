import 'package:dartz/dartz.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/user.dart';

/// Profile Repository Interface
abstract class ProfileRepository {
  /// 프로필 조회
  Future<Either<ApiException, User>> getProfile();

  /// 프로필 업데이트
  Future<Either<ApiException, User>> updateProfile({
    String? displayName,
    String? phoneNumber,
  });

  /// 프로필 이미지 업로드
  Future<Either<ApiException, String>> uploadProfileImage(String imagePath);

  /// 사용자 설정 조회
  Future<Either<ApiException, Map<String, dynamic>>> getSettings();

  /// 사용자 설정 업데이트
  Future<Either<ApiException, Map<String, dynamic>>> updateSettings(
      Map<String, dynamic> settings);

  /// 계정 삭제
  Future<Either<ApiException, void>> deleteAccount();
}
