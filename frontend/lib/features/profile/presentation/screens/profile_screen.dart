import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:frontend/core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/models/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
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

    // 로딩 중
    if (profileState.isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: Text(context.l10n.profile_title),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    // 로그인 안 됨
    if (!profileState.isAuthenticated || user == null) {
      return Scaffold(
        appBar: AppBar(
          title: Text(context.l10n.profile_title),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.account_circle_outlined,
                  size: 80,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(height: 24),
                Text(
                  context.l10n.auth_loginRequired,
                  style: AppTextStyles.h3,
                ),
                const SizedBox(height: 8),
                Text(
                  context.l10n.profile_loginPrompt,
                  style: AppTextStyles.body2.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () {
                    context.push('/login');
                  },
                  child: Text(context.l10n.auth_loginButton),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.profile_title),
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
                tabs: [
                  Tab(text: context.l10n.profile_savedPlacesTab),
                  Tab(text: context.l10n.profile_myCoursesTab),
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
            label: Text(context.l10n.profile_edit),
            onPressed: () {
              context.push('/profile/edit');
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
            label: context.l10n.profile_saved,
            count: stats.savedPlaces,
            onTap: () {},
          ),
          _buildStatCard(
            icon: Icons.favorite,
            label: context.l10n.profile_likes,
            count: stats.likedPlaces,
            onTap: () {},
          ),
          _buildStatCard(
            icon: Icons.map,
            label: context.l10n.profile_courses,
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
              'N',  // Display 'N' instead of count (temporary until API is connected)
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
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.bookmark_border,
            size: 64,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            context.l10n.profile_noSavedPlaces,
            style: AppTextStyles.h4,
          ),
          const SizedBox(height: 8),
          Text(
            context.l10n.place_savePlacePrompt,
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              context.go('/search');
            },
            child: Text(context.l10n.profile_findPlaces),
          ),
        ],
      ),
    );
  }

  Widget _buildMyCoursesTab() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.map_outlined,
            size: 64,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            context.l10n.profile_noCourses,
            style: AppTextStyles.h4,
          ),
          const SizedBox(height: 8),
          Text(
            context.l10n.profile_createCoursePrompt,
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              context.push('/courses/create');
            },
            child: Text(context.l10n.profile_createCourse),
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
            context.l10n.settings_title,
            style: AppTextStyles.h3.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),

          // Notifications
          SwitchListTile(
            title: Text(context.l10n.settings_notifications),
            subtitle: Text(context.l10n.settings_notificationsDesc),
            value: settings.notificationsEnabled,
            onChanged: (value) {
              ref.read(settingsProvider.notifier).setNotifications(value);
            },
          ),

          // Theme
          ListTile(
            title: Text(context.l10n.settings_theme),
            subtitle: Text(_getThemeLabel(context, settings.themeMode)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showThemeDialog(context, ref),
          ),

          // Language
          ListTile(
            title: Text(context.l10n.settings_language),
            subtitle: Text(settings.language == 'ko' ? context.l10n.settings_korean : 'English'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showLanguageDialog(context, ref),
          ),

          const Divider(height: 32),

          // App Info
          ListTile(
            title: Text(context.l10n.settings_appInfo),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showAppInfo(context),
          ),

          const Divider(height: 32),

          // Logout
          ListTile(
            title: Text(context.l10n.auth_logout),
            textColor: AppColors.error,
            leading: const Icon(Icons.logout, color: AppColors.error),
            onTap: () => _showLogoutDialog(context, ref),
          ),

          // Delete Account
          ListTile(
            title: Text(context.l10n.auth_deleteAccountTitle),
            textColor: AppColors.error,
            leading: const Icon(Icons.delete_forever, color: AppColors.error),
            onTap: () => _showDeleteAccountDialog(context, ref),
          ),
        ],
      ),
    );
  }

  String _getThemeLabel(BuildContext context, ThemeMode mode) {
    switch (mode) {
      case ThemeMode.system:
        return context.l10n.settings_themeSystem;
      case ThemeMode.light:
        return context.l10n.settings_themeLight;
      case ThemeMode.dark:
        return context.l10n.settings_themeDark;
    }
  }

  void _showThemeDialog(BuildContext context, WidgetRef ref) {
    final currentTheme = ref.read(settingsProvider).themeMode;

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.settings_selectTheme),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<ThemeMode>(
              title: Text(context.l10n.settings_themeSystem),
              value: ThemeMode.system,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(dialogContext);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: Text(context.l10n.settings_themeLight),
              value: ThemeMode.light,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(dialogContext);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: Text(context.l10n.settings_themeDark),
              value: ThemeMode.dark,
              groupValue: currentTheme,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setThemeMode(value);
                  Navigator.pop(dialogContext);
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
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.settings_selectLanguage),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<String>(
              title: Text(context.l10n.settings_korean),
              value: 'ko',
              groupValue: currentLanguage,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).setLanguage(value);
                  Navigator.pop(dialogContext);
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
                  Navigator.pop(dialogContext);
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
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.settings_appInfo),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${context.l10n.settings_appName}: ${packageInfo.appName}'),
            const SizedBox(height: 8),
            Text('${context.l10n.settings_version}: ${packageInfo.version}'),
            const SizedBox(height: 8),
            Text('${context.l10n.settings_buildNumber}: ${packageInfo.buildNumber}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.common_ok),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.auth_logout),
        content: Text(context.l10n.auth_logoutConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.common_cancel),
          ),
          TextButton(
            onPressed: () async {
              await ref.read(profileProvider.notifier).logout();
              if (!context.mounted) return;
              Navigator.pop(dialogContext); // Close dialog
              Navigator.pop(context); // Close bottom sheet
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(context.l10n.auth_logoutSuccess)),
              );
            },
            style: TextButton.styleFrom(
              foregroundColor: AppColors.error,
            ),
            child: Text(context.l10n.auth_logout),
          ),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.auth_deleteAccountTitle),
        content: Text(context.l10n.auth_deleteAccountConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.common_cancel),
          ),
          TextButton(
            onPressed: () async {
              try {
                await ref.read(authProvider.notifier).deleteAccount();
                if (!context.mounted) return;
                Navigator.pop(dialogContext); // Close dialog
                Navigator.pop(context); // Close bottom sheet
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(context.l10n.auth_deleteAccountSuccess)),
                );
              } catch (e) {
                if (!context.mounted) return;
                Navigator.pop(dialogContext);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('${context.l10n.auth_deleteAccountFailed}: $e')),
                );
              }
            },
            style: TextButton.styleFrom(
              foregroundColor: AppColors.error,
            ),
            child: Text(context.l10n.auth_deleteAccount),
          ),
        ],
      ),
    );
  }
}
