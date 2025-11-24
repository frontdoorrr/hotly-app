import 'dart:io';
import 'package:dio/dio.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/api_endpoints.dart';

/// Profile Remote Data Source
class ProfileRemoteDataSource {
  final DioClient _dioClient;

  ProfileRemoteDataSource(this._dioClient);

  /// 프로필 조회
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dioClient.get(ApiEndpoints.userProfile);
    return response.data as Map<String, dynamic>;
  }

  /// 프로필 업데이트
  Future<Map<String, dynamic>> updateProfile({
    String? displayName,
    String? phoneNumber,
  }) async {
    final data = <String, dynamic>{};
    if (displayName != null) data['display_name'] = displayName;
    if (phoneNumber != null) data['phone_number'] = phoneNumber;

    final response = await _dioClient.put(
      ApiEndpoints.userProfile,
      data: data,
    );
    return response.data as Map<String, dynamic>;
  }

  /// 프로필 이미지 업로드
  Future<Map<String, dynamic>> uploadProfileImage(String imagePath) async {
    final file = File(imagePath);
    final fileName = file.path.split('/').last;

    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(
        imagePath,
        filename: fileName,
      ),
    });

    final response = await _dioClient.post(
      ApiEndpoints.userProfileImage,
      data: formData,
    );
    return response.data as Map<String, dynamic>;
  }

  /// 사용자 설정 조회
  Future<Map<String, dynamic>> getSettings() async {
    final response = await _dioClient.get(ApiEndpoints.userSettings);
    return response.data as Map<String, dynamic>;
  }

  /// 사용자 설정 업데이트
  Future<Map<String, dynamic>> updateSettings(
      Map<String, dynamic> settings) async {
    final response = await _dioClient.put(
      ApiEndpoints.userSettings,
      data: settings,
    );
    return response.data as Map<String, dynamic>;
  }

  /// 계정 삭제
  Future<void> deleteAccount() async {
    await _dioClient.delete(ApiEndpoints.userDelete);
  }
}
