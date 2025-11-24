import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/profile_provider.dart';

class ProfileEditScreen extends ConsumerStatefulWidget {
  const ProfileEditScreen({super.key});

  @override
  ConsumerState<ProfileEditScreen> createState() => _ProfileEditScreenState();
}

class _ProfileEditScreenState extends ConsumerState<ProfileEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  bool _isLoading = false;
  String? _newImagePath;

  @override
  void initState() {
    super.initState();
    final user = ref.read(profileProvider).user;
    _nameController = TextEditingController(text: user?.name ?? '');
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileProvider);
    final user = profileState.user;

    if (user == null) {
      return Scaffold(
        appBar: AppBar(title: Text(context.l10n.profile_edit)),
        body: Center(child: Text(context.l10n.auth_loginRequired)),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.profile_edit),
        actions: [
          TextButton(
            onPressed: _isLoading ? null : _saveProfile,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(context.l10n.common_save),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              // Profile Image
              _buildProfileImage(user.profileImageUrl),
              const SizedBox(height: 32),

              // Name Field
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(
                  labelText: context.l10n.auth_name,
                  hintText: context.l10n.profile_nameHint,
                  prefixIcon: const Icon(Icons.person_outline),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return context.l10n.auth_nameRequired;
                  }
                  if (value.trim().length < 2) {
                    return context.l10n.auth_nameTooShort;
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Email Field (read-only)
              TextFormField(
                initialValue: user.email,
                decoration: InputDecoration(
                  labelText: context.l10n.auth_email,
                  prefixIcon: const Icon(Icons.email_outlined),
                ),
                readOnly: true,
                enabled: false,
              ),
              const SizedBox(height: 16),

              // Provider Info
              if (user.provider != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.gray100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _getProviderIcon(user.provider!),
                        color: AppColors.textSecondary,
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '${_getProviderName(context, user.provider!)} ${context.l10n.profile_loggedInWith}',
                        style: AppTextStyles.body2.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 24),

              // Account Created Date
              if (user.createdAt != null)
                Row(
                  children: [
                    const Icon(
                      Icons.calendar_today,
                      size: 16,
                      color: AppColors.textSecondary,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${context.l10n.profile_joinDate}: ${_formatDate(user.createdAt!)}',
                      style: AppTextStyles.labelSmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileImage(String? imageUrl) {
    return Stack(
      children: [
        CircleAvatar(
          radius: 60,
          backgroundColor: AppColors.primaryLight,
          backgroundImage: _newImagePath != null
              ? AssetImage(_newImagePath!) as ImageProvider
              : (imageUrl != null ? NetworkImage(imageUrl) : null),
          child: (imageUrl == null && _newImagePath == null)
              ? const Icon(
                  Icons.person,
                  size: 60,
                  color: AppColors.primary,
                )
              : null,
        ),
        Positioned(
          bottom: 0,
          right: 0,
          child: CircleAvatar(
            radius: 18,
            backgroundColor: AppColors.primary,
            child: IconButton(
              icon: const Icon(
                Icons.camera_alt,
                size: 18,
                color: Colors.white,
              ),
              onPressed: _pickImage,
              padding: EdgeInsets.zero,
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 512,
      maxHeight: 512,
      imageQuality: 80,
    );

    if (pickedFile != null) {
      setState(() {
        _newImagePath = pickedFile.path;
      });

      // 백엔드 API를 통해 이미지 업로드
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.l10n.profile_imageUploading)),
      );

      final imageUrl = await ref
          .read(profileProvider.notifier)
          .uploadProfileImage(pickedFile.path);

      if (!mounted) return;

      if (imageUrl != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.profile_imageUpdateSuccess)),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.profile_imageUpdateFailed)),
        );
      }
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final newName = _nameController.text.trim();

      // 백엔드 API를 통해 프로필 업데이트
      final success = await ref.read(profileProvider.notifier).updateProfile(
            displayName: newName,
          );

      if (!mounted) return;

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.profile_updateSuccess)),
        );
        context.pop();
      } else {
        final error = ref.read(profileProvider).error;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${context.l10n.profile_updateFailed}: $error')),
        );
      }
    } catch (e) {
      AppLogger.e('Failed to update profile', tag: 'ProfileEdit', error: e);
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${context.l10n.profile_updateFailed}: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  IconData _getProviderIcon(String provider) {
    switch (provider) {
      case 'google':
        return Icons.g_mobiledata;
      case 'apple':
        return Icons.apple;
      case 'kakao':
        return Icons.chat_bubble;
      default:
        return Icons.email;
    }
  }

  String _getProviderName(BuildContext context, String provider) {
    switch (provider) {
      case 'google':
        return 'Google';
      case 'apple':
        return 'Apple';
      case 'kakao':
        return context.l10n.auth_providerKakao;
      default:
        return context.l10n.auth_providerEmail;
    }
  }

  String _formatDate(DateTime date) {
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}';
  }
}
