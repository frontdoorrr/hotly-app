import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/models/user.dart';
import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileProvider);
    final user = profileState.user;

    if (profileState.isLoading || user == null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('프로필'),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('프로필'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              _showSettingsBottomSheet(context);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(profileProvider.notifier).refresh(),
        child: CustomScrollView(
          slivers: [
            // User Info Section
            SliverToBoxAdapter(
              child: _buildUserInfoSection(user),
            ),

            // Stats Section
            SliverToBoxAdapter(
              child: _buildStatsSection(profileState.stats),
            ),

            const SliverToBoxAdapter(
              child: Divider(height: 32),
            ),

            // Tabs
            SliverToBoxAdapter(
              child: TabBar(
                controller: _tabController,
                labelColor: AppColors.primary,
                unselectedLabelColor: AppColors.textSecondary,
                indicatorColor: AppColors.primary,
                tabs: const [
                  Tab(text: '저장된 장소'),
                  Tab(text: '내 코스'),
                ],
              ),
            ),

            // Tab Content
            SliverFillRemaining(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildSavedPlacesTab(),
                  _buildMyCoursesTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUserInfoSection(User user) {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: AppColors.primaryLight,
            backgroundImage: user.profileImageUrl != null
                ? NetworkImage(user.profileImageUrl!)
                : null,
            child: user.profileImageUrl == null
                ? const Icon(
                    Icons.person,
                    size: 50,
                    color: AppColors.primary,
                  )
                : null,
          ),
          const SizedBox(height: 16),
          Text(
            user.name,
            style: AppTextStyles.h2.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            user.email,
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.edit),
            label: const Text('프로필 편집'),
            onPressed: () {
              // TODO: Navigate to profile edit screen
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('프로필 편집 기능 개발 중')),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatsSection(UserStats? stats) {
    if (stats == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildStatCard(
            icon: Icons.bookmark,
            label: '저장',
            count: stats.savedPlaces,
            onTap: () {},
          ),
          _buildStatCard(
            icon: Icons.favorite,
            label: '좋아요',
            count: stats.likedPlaces,
            onTap: () {},
          ),
          _buildStatCard(
            icon: Icons.map,
            label: '코스',
            count: stats.courses,
            onTap: () {
              context.push('/courses/create');
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required int count,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(
              icon,
              size: 32,
              color: AppColors.primary,
            ),
            const SizedBox(height: 8),
            Text(
              '$count',
              style: AppTextStyles.h3.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTextStyles.label2.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSavedPlacesTab() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.bookmark_border,
            size: 64,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            '저장된 장소가 없습니다',
            style: AppTextStyles.h4,
          ),
          const SizedBox(height: 8),
          Text(
            '마음에 드는 장소를 저장해보세요',
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              context.go('/search');
            },
            child: const Text('장소 찾기'),
          ),
        ],
      ),
    );
  }

  Widget _buildMyCoursesTab() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.map_outlined,
            size: 64,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            '생성한 코스가 없습니다',
            style: AppTextStyles.h4,
          ),
          const SizedBox(height: 8),
          Text(
            '나만�� 데이트 코스를 만들어보세요',
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              context.push('/courses/create');
            },
            child: const Text('코스 만들기'),
          ),
        ],
      ),
    );
  }

  void _showSettingsBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) {
          return _SettingsSheet(scrollController: scrollController);
        },
      ),
    );
  }
}

class _SettingsSheet extends ConsumerWidget {
  final ScrollController scrollController;

  const _SettingsSheet({required this.scrollController});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return Container(
      padding: const EdgeInsets.all(16),
      child: ListView(
        controller: scrollController,
        children: [
          // Handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppColors.textSecondary.withOpacity(0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          Text(
            '설정',
            style: AppTextStyles.h3.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),

          // Notifications
          SwitchListTile(
            title: const Text('알림 설정'),
            subtitle: const Text('푸시 알림 받기'),
            value: settings.notificationsEnabled,
            onChanged: (value) {
              ref.read(settingsProvider.notifier).setNotifications(value);
            },
          ),

          // Theme
          ListTile(
            title: const Text('테마'),
            subtitle: Text(_getThemeLabel(settings.themeMode)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showThemeDialog(context, ref),
          ),

          // Language
          ListTile(
            title: const Text('언어'),
            subtitle: Text(settings.language == 'ko' ? '한국어' : 'English'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showLanguageDialog(context, ref),
          ),

          const Divider(height: 32),

          // App Info
          ListTile(
            title: const Text('앱 정보'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showAppInfo(context),
          ),

          const Divider(height: 32),

          // Logout
          ListTile(
            title: const Text('로그아웃'),
            textColor: AppColors.error,
            leading: const Icon(Icons.logout, color: AppColors.error),
            onTap: () => _showLogoutDialog(context, ref),
          ),
        ],
      ),
    );
  }

  String _getThemeLabel(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.system:
        return '시스템 설정';
      case ThemeMode.light:
        return '라이트 모드';
      case ThemeMode.dark:
        return '다크 모드';
    }
  }

  void _showThemeDialog(BuildContext context, WidgetRef ref) {
    final currentTheme = ref.read(settingsProvider).themeMode;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('테마 선택'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<ThemeMode>(
              title: const Text('시스템 설정'),
              value: ThemeMode.system,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: const Text('라이트 모드'),
              value: ThemeMode.light,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: const Text('다크 모드'),
              value: ThemeMode.dark,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showLanguageDialog(BuildContext context, WidgetRef ref) {
    final currentLanguage = ref.read(settingsProvider).language;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('언어 선택'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<String>(
              title: const Text('한국어'),
              value: 'ko',
              groupValue: currentLanguage,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setLanguage(value);
                  Navigator.pop(context);
                }
              },
            ),
            RadioListTile<String>(
              title: const Text('English'),
              value: 'en',
              groupValue: currentLanguage,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setLanguage(value);
                  Navigator.pop(context);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showAppInfo(BuildContext context) async {
    final packageInfo = await PackageInfo.fromPlatform();

    if (!context.mounted) return;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('앱 정보'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('앱 이름: ${packageInfo.appName}'),
            const SizedBox(height: 8),
            Text('버전: ${packageInfo.version}'),
            const SizedBox(height: 8),
            Text('빌드 번호: ${packageInfo.buildNumber}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('확인'),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('로그아웃'),
        content: const Text('정말 로그아웃하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () async {
              await ref.read(profileProvider.notifier).logout();
              if (!context.mounted) return;
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Close bottom sheet
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('로그아웃되었습니다')),
              );
            },
            style: TextButton.styleFrom(
              foregroundColor: AppColors.error,
            ),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );
  }
}
