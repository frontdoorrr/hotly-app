import 'package:dartz/dartz.dart';
import '../../domain/entities/archived_content.dart';
import '../../domain/entities/content_type_info.dart';
import '../../domain/repositories/archive_repository.dart';
import '../datasources/archive_remote_datasource.dart';
import '../models/archive_model.dart';
import '../services/instagram_media_extractor.dart';

class ArchiveRepositoryImpl implements ArchiveRepository {
  final ArchiveRemoteDataSource _remote;

  ArchiveRepositoryImpl(this._remote);

  @override
  Future<Either<Exception, ArchivedContent>> archiveUrl(
    String url, {
    bool force = false,
    String language = 'ko',
  }) async {
    try {
      final model = await _remote.archiveUrl(url, force: force, language: language);
      return Right(model.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, ArchivedContent>> archiveInstagram({
    required String url,
    required List<InstagramMediaFile> mediaFiles,
    String? caption,
    String? author,
    bool force = false,
    String language = 'ko',
  }) async {
    try {
      final model = await _remote.archiveInstagram(
        url: url,
        mediaFiles: mediaFiles,
        caption: caption,
        author: author,
        force: force,
        language: language,
      );
      return Right(model.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, List<ContentTypeInfo>>> getContentTypes() async {
    try {
      final models = await _remote.getContentTypes();
      return Right(models.map((m) => m.toEntity()).toList());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, ArchiveList>> getArchives({
    String? contentType,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final model = await _remote.getArchives(
        contentType: contentType,
        page: page,
        pageSize: pageSize,
      );
      return Right(model.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, ArchivedContent>> getArchive(String id) async {
    try {
      final model = await _remote.getArchive(id);
      return Right(model.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, void>> deleteArchive(String id) async {
    try {
      await _remote.deleteArchive(id);
      return const Right(null);
    } on Exception catch (e) {
      return Left(e);
    }
  }
}
