import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
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
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  // 앱이 포그라운드로 돌아올 때 (시스템 설정에서 돌아온 경우 포함) 재동기화
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(settingsProvider.notifier).syncWithOsPermission();
    }
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileProvider);
    final settings = ref.watch(settingsProvider);
    final user = profileState.user;

    if (profileState.isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text(context.l10n.profile_title)),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (!profileState.isAuthenticated || user == null) {
      return Scaffold(
        appBar: AppBar(title: Text(context.l10n.profile_title)),
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
                Text(context.l10n.auth_loginRequired, style: AppTextStyles.h3),
                const SizedBox(height: 8),
                Text(
                  context.l10n.profile_loginPrompt,
                  style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () => context.push('/login'),
                  child: Text(context.l10n.auth_loginButton),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.profile_title)),
      body: RefreshIndicator(
        onRefresh: () => ref.read(profileProvider.notifier).refresh(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildUserInfoSection(user),
              _buildArchiveCountSection(profileState.stats),
              const Divider(height: 8, thickness: 8, color: Color(0xFFF5F5F5)),
              _buildSettingsSection(settings),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUserInfoSection(User user) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
      child: Column(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: AppColors.primaryLight,
            backgroundImage: user.profileImageUrl != null
                ? NetworkImage(user.profileImageUrl!)
                : null,
            child: user.profileImageUrl == null
                ? const Icon(Icons.person, size: 50, color: AppColors.primary)
                : null,
          ),
          const SizedBox(height: 16),
          Text(
            user.name,
            style: AppTextStyles.h2.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            user.email,
            style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.edit),
            label: Text(context.l10n.profile_edit),
            onPressed: () => context.push('/profile/edit'),
          ),
        ],
      ),
    );
  }

  Widget _buildArchiveCountSection(UserStats? stats) {
    final count = stats?.savedPlaces ?? 0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Center(
        child: Column(
          children: [
            Text(
              '$count',
              style: AppTextStyles.h2.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              context.l10n.profile_archivingLabel,
              style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsSection(AppSettings settings) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
          child: Text(
            context.l10n.settings_title,
            style: AppTextStyles.label1.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        SwitchListTile(
          title: Text(context.l10n.settings_notifications),
          subtitle: Text(context.l10n.settings_notificationsDesc),
          value: settings.notificationsEnabled,
          onChanged: (value) async {
            final result =
                await ref.read(settingsProvider.notifier).setNotifications(value);
            if (!mounted) return;
            if (result == NotificationToggleResult.permanentlyDenied) {
              _showOpenSettingsDialog();
            }
          },
        ),
        ListTile(
          title: Text(context.l10n.settings_theme),
          subtitle: Text(_getThemeLabel(settings.themeMode)),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showThemeDialog(),
        ),
        ListTile(
          title: Text(context.l10n.settings_language),
          subtitle: Text(settings.language == 'ko'
              ? context.l10n.settings_korean
              : 'English'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showLanguageDialog(),
        ),
        const Divider(),
        ListTile(
          title: Text(context.l10n.settings_appInfo),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showAppInfo(),
        ),
        const Divider(),
        ListTile(
          title: Text(context.l10n.auth_logout),
          textColor: AppColors.error,
          leading: const Icon(Icons.logout, color: AppColors.error),
          onTap: () => _showLogoutDialog(),
        ),
        ListTile(
          title: Text(context.l10n.auth_deleteAccountTitle),
          textColor: AppColors.error,
          leading: const Icon(Icons.delete_forever, color: AppColors.error),
          onTap: () => _showDeleteAccountDialog(),
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  String _getThemeLabel(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.system:
        return context.l10n.settings_themeSystem;
      case ThemeMode.light:
        return context.l10n.settings_themeLight;
      case ThemeMode.dark:
        return context.l10n.settings_themeDark;
    }
  }

  void _showOpenSettingsDialog() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.settings_notificationPermissionTitle),
        content: Text(context.l10n.settings_notificationPermissionBody),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.common_cancel),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              openAppSettings();
            },
            child: Text(context.l10n.settings_openSystemSettings),
          ),
        ],
      ),
    );
  }

  void _showThemeDialog() {
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

  void _showLanguageDialog() {
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

  Future<void> _showAppInfo() async {
    final packageInfo = await PackageInfo.fromPlatform();
    if (!mounted) return;
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

  void _showLogoutDialog() {
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
              Navigator.pop(dialogContext);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(context.l10n.auth_logoutSuccess)),
              );
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: Text(context.l10n.auth_logout),
          ),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog() {
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
                Navigator.pop(dialogContext);
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
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: Text(context.l10n.auth_deleteAccount),
          ),
        ],
      ),
    );
  }
}
