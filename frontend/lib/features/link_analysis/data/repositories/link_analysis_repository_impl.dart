import 'package:dartz/dartz.dart';
import '../../domain/entities/link_analysis_result.dart';
import '../../domain/repositories/link_analysis_repository.dart';
import '../datasources/link_analysis_remote_datasource.dart';
import '../models/link_analysis_response.dart';

/// Implementation of LinkAnalysisRepository
class LinkAnalysisRepositoryImpl implements LinkAnalysisRepository {
  final LinkAnalysisRemoteDataSource _remoteDataSource;

  LinkAnalysisRepositoryImpl(this._remoteDataSource);

  @override
  Future<Either<Exception, LinkAnalysisResult>> analyzeLink({
    required String url,
    bool forceRefresh = false,
  }) async {
    try {
      final response = await _remoteDataSource.analyzeLink(
        url: url,
        forceRefresh: forceRefresh,
      );

      return Right(response.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, LinkAnalysisResult>> getAnalysisStatus(
    String analysisId,
  ) async {
    try {
      final response = await _remoteDataSource.getAnalysisStatus(analysisId);
      return Right(response.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, void>> cancelAnalysis(String analysisId) async {
    try {
      await _remoteDataSource.cancelAnalysis(analysisId);
      return const Right(null);
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, Map<String, dynamic>>> saveAnalyzedPlace(
    String analysisId, {
    String? sourceUrl,
  }) async {
    try {
      final response = await _remoteDataSource.saveAnalyzedPlace(
        analysisId,
        sourceUrl: sourceUrl,
      );
      return Right(response);
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  bool isUrlSupported(String url) {
    // Supported platforms based on backend ContentExtractor
    final supportedPlatforms = [
      'instagram.com',
      'naver.com/blog',
      'blog.naver.com',
      'youtube.com',
      'youtu.be',
    ];

    return supportedPlatforms.any((platform) => url.contains(platform));
  }
}
