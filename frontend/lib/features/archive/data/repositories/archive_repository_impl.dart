import 'package:dartz/dartz.dart';
import '../../domain/entities/archived_content.dart';
import '../../domain/repositories/archive_repository.dart';
import '../datasources/archive_remote_datasource.dart';
import '../models/archive_model.dart';

class ArchiveRepositoryImpl implements ArchiveRepository {
  final ArchiveRemoteDataSource _remote;

  ArchiveRepositoryImpl(this._remote);

  @override
  Future<Either<Exception, ArchivedContent>> archiveUrl(
    String url, {
    bool force = false,
  }) async {
    try {
      final model = await _remote.archiveUrl(url, force: force);
      return Right(model.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, ArchiveList>> getArchives({
    ContentType? contentType,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final model = await _remote.getArchives(
        contentType: contentType?.name,
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
