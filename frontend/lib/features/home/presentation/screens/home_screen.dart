import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/storage/local_storage.dart';
import '../../../link_analysis/presentation/widgets/link_input_bottom_sheet.dart';
import '../providers/home_provider.dart';
import '../widgets/place_card.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // 화면 로드 시 데이터 가져오기
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
  }

  Future<void> _loadData() async {
    final (lat, lng) = LocalStorage.instance.lastLocation;
    await ref.read(homeProvider.notifier).refreshAll(lat, lng);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(homeProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(Icons.local_fire_department, color: theme.colorScheme.primary),
            const SizedBox(width: AppTheme.space2),
            const Text('Hotly'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {
              // TODO: 알림 화면으로 이동
            },
          ),
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () {
              // TODO: 프로필 화면으로 이동
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: CustomScrollView(
          slivers: [
            // 추천 장소 섹션
            SliverToBoxAdapter(
              child: _buildRecommendedSection(state),
            ),

            // 빠른 액세스
            SliverToBoxAdapter(
              child: _buildQuickActionsSection(context),
            ),

            // 인기 장소 섹션
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(AppTheme.space4),
                child: Text(
                  '인기 장소',
                  style: theme.textTheme.titleLarge,
                ),
              ),
            ),

            // 인기 장소 그리드
            if (state.isLoadingPopular)
              const SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: EdgeInsets.all(AppTheme.space8),
                    child: CircularProgressIndicator(),
                  ),
                ),
              )
            else if (state.popularPlaces.isEmpty)
              SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(AppTheme.space8),
                    child: Text(
                      '인기 장소가 없습니다',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ),
              )
            else
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4),
                sliver: SliverGrid(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.85,
                    crossAxisSpacing: AppTheme.space3,
                    mainAxisSpacing: AppTheme.space3,
                  ),
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final place = state.popularPlaces[index];
                      return PlaceCard(
                        place: place,
                        isHorizontal: false,
                        onTap: () {
                          context.push('/places/${place.id}');
                        },
                      );
                    },
                    childCount: state.popularPlaces.length,
                  ),
                ),
              ),

            // 하단 여백
            const SliverToBoxAdapter(
              child: SizedBox(height: AppTheme.space8),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => LinkInputBottomSheet.show(context),
        icon: const Icon(Icons.link),
        label: const Text('링크 분석'),
        backgroundColor: theme.colorScheme.primary,
        foregroundColor: Colors.white,
      ),
    );
  }

  Widget _buildRecommendedSection(HomeState state) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.all(AppTheme.space4),
          child: Row(
            children: [
              Icon(
                Icons.local_fire_department,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(width: AppTheme.space2),
              Text(
                '오늘의 추천 장소',
                style: theme.textTheme.titleLarge,
              ),
            ],
          ),
        ),

        if (state.isLoadingRecommended)
          const SizedBox(
            height: 120,
            child: Center(child: CircularProgressIndicator()),
          )
        else if (state.recommendedPlaces.isEmpty)
          SizedBox(
            height: 120,
            child: Center(
              child: Text(
                '추천 장소가 없습니다',
                style: theme.textTheme.bodyMedium,
              ),
            ),
          )
        else
          SizedBox(
            height: 120,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4),
              itemCount: state.recommendedPlaces.length,
              itemBuilder: (context, index) {
                final place = state.recommendedPlaces[index];
                return Padding(
                  padding: const EdgeInsets.only(right: AppTheme.space3),
                  child: PlaceCard(
                    place: place,
                    isHorizontal: true,
                    onTap: () {
                      context.push('/places/${place.id}');
                    },
                  ),
                );
              },
            ),
          ),

        if (state.recommendedPlaces.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4),
            child: TextButton(
              onPressed: () {
                // TODO: 추천 장소 전체 보기
              },
              child: const Text('더보기 →'),
            ),
          ),
      ],
    );
  }

  Widget _buildQuickActionsSection(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(AppTheme.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '빠른 액세스',
            style: theme.textTheme.titleLarge,
          ),
          const SizedBox(height: AppTheme.space3),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildQuickActionButton(
                context,
                icon: Icons.link,
                label: '링크\n분석',
                onTap: () => LinkInputBottomSheet.show(context),
              ),
              _buildQuickActionButton(
                context,
                icon: Icons.search,
                label: '장소\n검색',
                onTap: () {
                  context.push('/search');
                },
              ),
              _buildQuickActionButton(
                context,
                icon: Icons.map,
                label: '지도\n보기',
                onTap: () {
                  context.push('/map');
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    final theme = Theme.of(context);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppTheme.radiusLg),
      child: Container(
        width: 100,
        padding: const EdgeInsets.all(AppTheme.space4),
        decoration: BoxDecoration(
          border: Border.all(
            color: theme.colorScheme.outline.withOpacity(0.3),
          ),
          borderRadius: BorderRadius.circular(AppTheme.radiusLg),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              size: 32,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: AppTheme.space2),
            Text(
              label,
              textAlign: TextAlign.center,
              style: theme.textTheme.labelSmall,
            ),
          ],
        ),
      ),
    );
  }
}
