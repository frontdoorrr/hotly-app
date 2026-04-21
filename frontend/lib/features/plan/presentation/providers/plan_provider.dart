import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../archive/domain/entities/archived_content.dart';
import '../../../archive/presentation/providers/archive_provider.dart';

final planEventProvider = FutureProvider<List<ArchivedContent>>((ref) async {
  final repo = ref.watch(archiveRepositoryProvider);
  final result = await repo.getArchives(
    contentType: 'event',
    page: 1,
    pageSize: 50,
  );
  return result.fold((e) => throw e, (list) => list.items);
});

final planPlaceProvider = FutureProvider<List<ArchivedContent>>((ref) async {
  final repo = ref.watch(archiveRepositoryProvider);
  final result = await repo.getArchives(
    contentType: 'place',
    page: 1,
    pageSize: 50,
  );
  return result.fold((e) => throw e, (list) => list.items);
});
