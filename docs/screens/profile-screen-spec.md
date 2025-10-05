# 프로필 화면 스펙 (Profile Screen Specification)

## 문서 정보
- **화면명**: 프로필 화면 (Profile Screen)
- **라우트**: `/profile`
- **버전**: 1.0
- **작성일**: 2025-01-XX

---

## 1. 화면 목적

- 사용자 정보 및 통계 표시
- 저장된 장소/코스 관리
- 앱 설정 및 계정 관리

---

## 2. 와이어프레임

```
┌─────────────────────────────────────┐
│  프로필                   ⚙️        │ ← App Bar
├─────────────────────────────────────┤
│  ┌────┐                             │
│  │ 🧑 │  김민지                     │ ← User Info
│  └────┘  user@email.com             │
│          [프로필 편집]              │
│                                     │
│  ┌───────┬───────┬────────┐        │
│  │ 저장  │ 좋아요│  코스  │        │ ← Stats
│  │  24   │  48   │   6    │        │
│  └───────┴───────┴────────┘        │
│                                     │
│  ──────────────────────────────────│
│                                     │
│  [저장된 장소] [내 코스]           │ ← Tabs
│  ────────                           │
│                                     │
│  전체 (24)        [편집]           │
│                                     │
│  📁 기본 폴더 (10)                 │ ← Folders
│  📁 데이트 (8)                     │
│  📁 맛집 (6)                       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ┌────┐ 카페 A               │   │ ← Place Card
│  │ │IMG │ ⭐ 4.5 · 500m       │   │
│  │ └────┘ #데이트              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ──────────────────────────────────│
│                                     │
│  설정                               │ ← Settings
│  • 알림 설정                       │
│  • 테마 (시스템/라이트/다크)        │
│  • 언어                            │
│  • 정보                            │
│  • 로그아웃                        │
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리

```dart
ProfileScreen (ConsumerStatefulWidget)
└─ Scaffold
   ├─ AppBar
   │  ├─ Title: "프로필"
   │  └─ Actions: [SettingsButton]
   │
   ├─ Body: CustomScrollView
   │  └─ SliverList
   │     ├─ UserInfoSection
   │     │  ├─ CircleAvatar (프로필 이미지)
   │     │  ├─ UserName & Email
   │     │  └─ EditProfileButton
   │     │
   │     ├─ StatsSection
   │     │  ├─ StatCard (저장)
   │     │  ├─ StatCard (좋아요)
   │     │  └─ StatCard (코스)
   │     │
   │     ├─ TabBar (저장된 장소 / 내 코스)
   │     │
   │     ├─ SavedPlacesTab (when selected)
   │     │  ├─ FolderList
   │     │  └─ PlaceList
   │     │
   │     ├─ MyCoursesTab (when selected)
   │     │  └─ CourseList
   │     │
   │     └─ SettingsSection
   │        ├─ NotificationSettings
   │        ├─ ThemeSettings
   │        ├─ LanguageSettings
   │        ├─ AppInfo
   │        └─ LogoutButton
```

---

## 4. 핵심 컴포넌트

### 4.1 UserInfoSection

```dart
class UserInfoSection extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          CircleAvatar(
            radius: 40,
            backgroundImage: user.profileImage != null
                ? NetworkImage(user.profileImage!)
                : null,
            child: user.profileImage == null
                ? const Icon(Icons.person, size: 40)
                : null,
          ),
          const SizedBox(height: 16),
          Text(
            user.name,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          Text(
            user.email,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: () => context.push('/profile/edit'),
            child: const Text('프로필 편집'),
          ),
        ],
      ),
    );
  }
}
```

### 4.2 StatsSection

```dart
class StatsSection extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(userStatsProvider);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        StatCard(
          icon: Icons.bookmark,
          label: '저장',
          count: stats.savedPlaces,
          onTap: () => _navigateToSaved(context),
        ),
        StatCard(
          icon: Icons.favorite,
          label: '좋아요',
          count: stats.likedPlaces,
          onTap: () => _navigateToLiked(context),
        ),
        StatCard(
          icon: Icons.map,
          label: '코스',
          count: stats.courses,
          onTap: () => _navigateToCourses(context),
        ),
      ],
    );
  }
}

class StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final int count;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Column(
        children: [
          Icon(icon, size: 32),
          const SizedBox(height: 8),
          Text(
            '$count',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
```

### 4.3 FolderList

```dart
class FolderList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final folders = ref.watch(foldersProvider);

    return Column(
      children: [
        ListTile(
          leading: const Icon(Icons.folder_open),
          title: Text('전체 (${folders.totalCount})'),
          trailing: TextButton(
            onPressed: () => _showEditMode(context),
            child: const Text('편집'),
          ),
        ),
        ...folders.map((folder) => FolderTile(folder: folder)),
      ],
    );
  }
}

class FolderTile extends StatelessWidget {
  final Folder folder;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: const Icon(Icons.folder),
      title: Text('${folder.name} (${folder.count})'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => context.push('/folders/${folder.id}'),
    );
  }
}
```

---

## 5. 상태 관리

```dart
// User Provider
final currentUserProvider = StateNotifierProvider<UserNotifier, User>((ref) {
  return UserNotifier();
});

class UserNotifier extends StateNotifier<User> {
  UserNotifier() : super(User.initial());

  Future<void> loadUser() async {
    // Load user from API/storage
  }

  Future<void> updateProfile(UserProfile profile) async {
    // Update user profile
  }
}

// Stats Provider
final userStatsProvider = FutureProvider<UserStats>((ref) async {
  final userId = ref.watch(currentUserProvider).id;
  return await ref.read(statsRepositoryProvider).getStats(userId);
});

// Folders Provider
final foldersProvider = FutureProvider<List<Folder>>((ref) async {
  final userId = ref.watch(currentUserProvider).id;
  return await ref.read(folderRepositoryProvider).getFolders(userId);
});

// Settings Provider
final settingsProvider = StateNotifierProvider<SettingsNotifier, AppSettings>((ref) {
  return SettingsNotifier();
});

class SettingsNotifier extends StateNotifier<AppSettings> {
  SettingsNotifier() : super(AppSettings.initial());

  void setTheme(ThemeMode mode) {
    state = state.copyWith(themeMode: mode);
  }

  void setNotifications(bool enabled) {
    state = state.copyWith(notificationsEnabled: enabled);
  }
}

@freezed
class AppSettings with _$AppSettings {
  const factory AppSettings({
    required ThemeMode themeMode,
    required bool notificationsEnabled,
    required String language,
  }) = _AppSettings;

  factory AppSettings.initial() => const AppSettings(
    themeMode: ThemeMode.system,
    notificationsEnabled: true,
    language: 'ko',
  );
}
```

---

## 6. 설정 화면

### 6.1 SettingsSection

```dart
class SettingsSection extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            '설정',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),

        // 알림 설정
        SwitchListTile(
          title: const Text('알림 설정'),
          subtitle: const Text('푸시 알림 받기'),
          value: settings.notificationsEnabled,
          onChanged: (value) {
            ref.read(settingsProvider.notifier).setNotifications(value);
          },
        ),

        // 테마 설정
        ListTile(
          title: const Text('테마'),
          subtitle: Text(_getThemeLabel(settings.themeMode)),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showThemeDialog(context, ref),
        ),

        // 언어 설정
        ListTile(
          title: const Text('언어'),
          subtitle: Text(settings.language == 'ko' ? '한국어' : 'English'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showLanguageDialog(context, ref),
        ),

        // 앱 정보
        ListTile(
          title: const Text('정보'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => context.push('/about'),
        ),

        const Divider(),

        // 로그아웃
        ListTile(
          title: const Text('로그아웃'),
          textColor: Theme.of(context).colorScheme.error,
          onTap: () => _showLogoutDialog(context, ref),
        ),
      ],
    );
  }

  String _getThemeLabel(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.system:
        return '시스템';
      case ThemeMode.light:
        return '라이트';
      case ThemeMode.dark:
        return '다크';
    }
  }
}
```

---

## 7. 완료 정의 (DoD)

- [ ] 사용자 정보 표시 (이름, 이메일, 프로필 이미지)
- [ ] 통계 섹션 (저장, 좋아요, 코스 개수)
- [ ] 저장된 장소 탭 (폴더별 관리)
- [ ] 내 코스 탭 (생성한 코스 목록)
- [ ] 설정 기능 (알림, 테마, 언어)
- [ ] 로그아웃 기능
- [ ] 프로필 편집 네비게이션

---

## 8. 수용 기준

- **Given** 로그인된 사용자
- **When** 프로필 화면 진입
- **Then** 사용자 정보 및 통계 정확히 표시

- **Given** 저장된 장소가 있는 상태
- **When** 저장된 장소 탭 선택
- **Then** 폴더별로 장소 목록 표시

- **Given** 테마 설정 변경
- **When** 다크 모드 선택
- **Then** 즉시 다크 테마 적용 및 저장

---

*작성일: 2025-01-XX*
*작성자: Claude*
*버전: 1.0*