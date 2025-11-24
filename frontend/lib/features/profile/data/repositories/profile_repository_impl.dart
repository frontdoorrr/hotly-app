import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/user.dart';
import '../../domain/repositories/profile_repository.dart';
import '../datasources/profile_remote_datasource.dart';

/// Profile Repository Implementation
class ProfileRepositoryImpl implements ProfileRepository {
  final ProfileRemoteDataSource remoteDataSource;

  ProfileRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<ApiException, User>> getProfile() async {
    try {
      final data = await remoteDataSource.getProfile();
      final user = User(
        id: (data['id'] ?? '') as String,
        email: (data['email'] ?? '') as String,
        name: (data['display_name'] ?? '') as String,
        profileImageUrl: data['profile_image_url'] as String?,
        phoneNumber: data['phone_number'] as String?,
        createdAt: data['created_at'] != null
            ? DateTime.parse(data['created_at'] as String)
            : null,
      );
      return Right(user);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, User>> updateProfile({
    String? displayName,
    String? phoneNumber,
  }) async {
    try {
      final data = await remoteDataSource.updateProfile(
        displayName: displayName,
        phoneNumber: phoneNumber,
      );
      final user = User(
        id: (data['id'] ?? '') as String,
        email: (data['email'] ?? '') as String,
        name: (data['display_name'] ?? '') as String,
        profileImageUrl: data['profile_image_url'] as String?,
        phoneNumber: data['phone_number'] as String?,
        createdAt: data['created_at'] != null
            ? DateTime.parse(data['created_at'] as String)
            : null,
      );
      AppLogger.d('Profile updated successfully', tag: 'ProfileRepo');
      return Right(user);
    } on ApiException catch (e) {
      AppLogger.e('Failed to update profile: ${e.message}', tag: 'ProfileRepo');
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, String>> uploadProfileImage(
      String imagePath) async {
    try {
      final data = await remoteDataSource.uploadProfileImage(imagePath);
      final imageUrl = data['image_url'] as String? ?? '';
      AppLogger.d('Profile image uploaded: $imageUrl', tag: 'ProfileRepo');
      return Right(imageUrl);
    } on ApiException catch (e) {
      AppLogger.e('Failed to upload image: ${e.message}', tag: 'ProfileRepo');
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, Map<String, dynamic>>> getSettings() async {
    try {
      final data = await remoteDataSource.getSettings();
      return Right(data);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, Map<String, dynamic>>> updateSettings(
      Map<String, dynamic> settings) async {
    try {
      final data = await remoteDataSource.updateSettings(settings);
      return Right(data);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, void>> deleteAccount() async {
    try {
      await remoteDataSource.deleteAccount();
      return const Right(null);
    } on ApiException catch (e) {
      return Left(e);
    }
  }
}

/// Profile Repository Provider
final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  final remoteDataSource = ProfileRemoteDataSource(dioClient);
  return ProfileRepositoryImpl(remoteDataSource);
});
