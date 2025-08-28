# TRD: 앱 온보딩 및 초기 설정

## 1. 기술 개요
**목적:** PRD 06-onboarding-flow 요구사항을 충족하기 위한 사용자 친화적 온보딩 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- UI Framework: Flutter with Custom Animations
- 상태 관리: Riverpod + State Machine
- 로컬 저장소: Hive + SharedPreferences
- 분석: Firebase Analytics + Custom Events
- A/B 테스트: Firebase Remote Config + Custom Framework

---

## 2. 시스템 아키텍처

### 2-1. 온보딩 상태 흐름도
```
[App Launch] → [First Time Check]
    ↓              ↓
[Skip] ←── [Onboarding State Machine] → [Main App]
    ↓              ↓
[Guest Mode] → [Progressive Setup]
    ↓              ↓
[Conversion] → [Complete Profile]
```

### 2-2. 상태 관리 구조
```
OnboardingStateMachine
├── WelcomeState
├── FeatureIntroState  
├── BasicSetupState
├── PreferencesState
├── FirstExperienceState
└── CompletionState

각 State는 다음 속성을 가짐:
- canSkip: boolean
- isRequired: boolean
- completionCriteria: Function
- nextState: OnboardingState
```

---

## 3. Flutter 구현

### 3-1. 온보딩 상태 관리
```dart
// 온보딩 상태 정의
enum OnboardingStep {
  welcome,
  featureIntro,
  basicSetup,
  preferences,
  firstExperience,
  completion
}

// 온보딩 상태 모델
class OnboardingState {
  final OnboardingStep currentStep;
  final int totalSteps;
  final Map<OnboardingStep, bool> completedSteps;
  final Map<OnboardingStep, bool> skippedSteps;
  final UserPreferences preferences;
  final bool canSkip;
  
  const OnboardingState({
    required this.currentStep,
    required this.totalSteps,
    required this.completedSteps,
    required this.skippedSteps,
    required this.preferences,
    this.canSkip = true,
  });

  double get progress => (completedSteps.values.where((v) => v).length) / totalSteps;
  
  OnboardingState copyWith({
    OnboardingStep? currentStep,
    Map<OnboardingStep, bool>? completedSteps,
    Map<OnboardingStep, bool>? skippedSteps,
    UserPreferences? preferences,
    bool? canSkip,
  }) {
    return OnboardingState(
      currentStep: currentStep ?? this.currentStep,
      totalSteps: totalSteps,
      completedSteps: completedSteps ?? this.completedSteps,
      skippedSteps: skippedSteps ?? this.skippedSteps,
      preferences: preferences ?? this.preferences,
      canSkip: canSkip ?? this.canSkip,
    );
  }
}

// 사용자 선호도 모델
class UserPreferences {
  final String? region;
  final List<TransportMethod> transportMethods;
  final Map<InterestCategory, int> interests;
  final NotificationSettings notifications;
  final String theme;
  
  const UserPreferences({
    this.region,
    this.transportMethods = const [],
    this.interests = const {},
    this.notifications = const NotificationSettings(),
    this.theme = 'system',
  });

  bool get isComplete => 
    region != null && 
    transportMethods.isNotEmpty && 
    interests.isNotEmpty;
}

// 온보딩 컨트롤러 (Riverpod)
class OnboardingController extends StateNotifier<OnboardingState> {
  OnboardingController() : super(_initialState);
  
  static const _initialState = OnboardingState(
    currentStep: OnboardingStep.welcome,
    totalSteps: 6,
    completedSteps: {},
    skippedSteps: {},
    preferences: UserPreferences(),
  );

  Future<void> nextStep() async {
    final currentIndex = OnboardingStep.values.indexOf(state.currentStep);
    
    if (currentIndex < OnboardingStep.values.length - 1) {
      final nextStep = OnboardingStep.values[currentIndex + 1];
      
      // 현재 단계 완료 표시
      final newCompletedSteps = Map<OnboardingStep, bool>.from(state.completedSteps);
      newCompletedSteps[state.currentStep] = true;
      
      state = state.copyWith(
        currentStep: nextStep,
        completedSteps: newCompletedSteps,
      );
      
      // 진행 상황 저장
      await _saveProgress();
      
      // 분석 이벤트 전송
      await _trackStepCompleted(state.currentStep);
    }
  }

  Future<void> previousStep() async {
    final currentIndex = OnboardingStep.values.indexOf(state.currentStep);
    
    if (currentIndex > 0) {
      final previousStep = OnboardingStep.values[currentIndex - 1];
      state = state.copyWith(currentStep: previousStep);
    }
  }

  Future<void> skipStep() async {
    if (!state.canSkip) return;
    
    // 현재 단계 건너뛰기 표시
    final newSkippedSteps = Map<OnboardingStep, bool>.from(state.skippedSteps);
    newSkippedSteps[state.currentStep] = true;
    
    state = state.copyWith(skippedSteps: newSkippedSteps);
    
    // 분석 이벤트
    await _trackStepSkipped(state.currentStep);
    
    // 다음 단계로
    await nextStep();
  }

  Future<void> skipAllOnboarding() async {
    // 게스트 모드로 전환
    await _setGuestMode(true);
    await _trackOnboardingSkipped();
    
    // 메인 앱으로 이동
    _navigateToMainApp();
  }

  Future<void> updatePreferences(UserPreferences preferences) async {
    state = state.copyWith(preferences: preferences);
    await _savePreferences(preferences);
  }

  Future<void> completeOnboarding() async {
    // 온보딩 완료 표시
    await _setOnboardingCompleted(true);
    
    // 최종 설정 서버 동기화
    await _syncUserPreferences();
    
    // 완료 이벤트
    await _trackOnboardingCompleted();
    
    // 첫 체험 준비
    await _prepareFirstExperience();
  }

  Future<void> _saveProgress() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('onboarding_progress', jsonEncode({
      'currentStep': state.currentStep.toString(),
      'completedSteps': state.completedSteps.map((k, v) => MapEntry(k.toString(), v)),
      'skippedSteps': state.skippedSteps.map((k, v) => MapEntry(k.toString(), v)),
    }));
  }

  Future<void> _trackStepCompleted(OnboardingStep step) async {
    await FirebaseAnalytics.instance.logEvent(
      name: 'onboarding_step_completed',
      parameters: {
        'step': step.toString(),
        'step_number': OnboardingStep.values.indexOf(step) + 1,
        'total_time_ms': DateTime.now().millisecondsSinceEpoch - _startTime,
      },
    );
  }
}

final onboardingControllerProvider = StateNotifierProvider<OnboardingController, OnboardingState>(
  (ref) => OnboardingController(),
);
```

### 3-2. 온보딩 UI 위젯
```dart
class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingControllerProvider);
    final controller = ref.watch(onboardingControllerProvider.notifier);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // 진행률 표시
            OnboardingProgressBar(
              progress: state.progress,
              currentStep: state.currentStep,
            ),
            
            // 메인 콘텐츠
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) => _onPageChanged(index, controller),
                children: [
                  WelcomeScreen(),
                  FeatureIntroScreen(),
                  BasicSetupScreen(),
                  PreferencesScreen(),
                  FirstExperienceScreen(),
                  CompletionScreen(),
                ],
              ),
            ),
            
            // 하단 버튼
            OnboardingBottomBar(
              canGoBack: _canGoBack(state.currentStep),
              canSkip: state.canSkip,
              onBack: () => controller.previousStep(),
              onSkip: () => controller.skipStep(),
              onNext: () => controller.nextStep(),
              onSkipAll: () => controller.skipAllOnboarding(),
            ),
          ],
        ),
      ),
    );
  }
}

// 진행률 표시 위젯
class OnboardingProgressBar extends StatelessWidget {
  final double progress;
  final OnboardingStep currentStep;

  const OnboardingProgressBar({
    Key? key,
    required this.progress,
    required this.currentStep,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // 도트 인디케이터
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: OnboardingStep.values.asMap().entries.map((entry) {
              final index = entry.key;
              final step = entry.value;
              final isActive = index <= OnboardingStep.values.indexOf(currentStep);
              
              return AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.symmetric(horizontal: 4),
                width: isActive ? 12 : 8,
                height: isActive ? 12 : 8,
                decoration: BoxDecoration(
                  color: isActive ? Theme.of(context).primaryColor : Colors.grey[300],
                  shape: BoxShape.circle,
                ),
              );
            }).toList(),
          ),
          
          const SizedBox(height: 12),
          
          // 진행률 바
          LinearProgressIndicator(
            value: progress,
            backgroundColor: Colors.grey[200],
            valueColor: AlwaysStoppedAnimation<Color>(Theme.of(context).primaryColor),
          ),
          
          const SizedBox(height: 8),
          
          // 진행률 텍스트
          Text(
            '${(progress * 100).round()}% 완료',
            style: Theme.of(context).textTheme.caption?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }
}

// 하단 버튼 바
class OnboardingBottomBar extends StatelessWidget {
  final bool canGoBack;
  final bool canSkip;
  final VoidCallback? onBack;
  final VoidCallback? onSkip;
  final VoidCallback? onNext;
  final VoidCallback? onSkipAll;

  const OnboardingBottomBar({
    Key? key,
    this.canGoBack = false,
    this.canSkip = true,
    this.onBack,
    this.onSkip,
    this.onNext,
    this.onSkipAll,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey[200]!)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            // 이전 버튼
            if (canGoBack)
              OutlinedButton(
                onPressed: onBack,
                child: const Text('이전'),
              )
            else
              const SizedBox(width: 60),
            
            const Spacer(),
            
            // 전체 건너뛰기 (첫 번째 화면에만)
            if (canSkip)
              TextButton(
                onPressed: onSkipAll,
                child: Text(
                  '나중에',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ),
            
            const SizedBox(width: 12),
            
            // 건너뛰기 버튼
            if (canSkip)
              TextButton(
                onPressed: onSkip,
                child: const Text('건너뛰기'),
              ),
            
            const SizedBox(width: 12),
            
            // 다음/완료 버튼
            ElevatedButton(
              onPressed: onNext,
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(80, 44),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(22),
                ),
              ),
              child: const Text('다음'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 3-3. 기본 설정 화면
```dart
class BasicSetupScreen extends ConsumerStatefulWidget {
  const BasicSetupScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<BasicSetupScreen> createState() => _BasicSetupScreenState();
}

class _BasicSetupScreenState extends ConsumerState<BasicSetupScreen>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _slideAnimation;
  late Animation<double> _fadeAnimation;
  
  String? _selectedRegion;
  List<TransportMethod> _selectedTransportMethods = [];
  final Map<InterestCategory, int> _interestRatings = {};

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _loadCurrentSettings();
  }

  void _setupAnimations() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _slideAnimation = Tween<double>(
      begin: 0.3,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutBack,
    ));

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0.3, 1.0),
    ));

    _animationController.forward();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: Transform.scale(
            scale: _slideAnimation.value,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 제목
                  Text(
                    '기본 설정',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  
                  const SizedBox(height: 8),
                  
                  Text(
                    '더 나은 추천을 위해 몇 가지만 알려주세요',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // 지역 선택
                          _buildRegionSelection(),
                          
                          const SizedBox(height: 32),
                          
                          // 이동수단 선택
                          _buildTransportMethodSelection(),
                          
                          const SizedBox(height: 32),
                          
                          // 관심 분야 선택
                          _buildInterestSelection(),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildRegionSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.location_on, color: Theme.of(context).primaryColor),
            const SizedBox(width: 8),
            Text(
              '주로 어느 지역에서 데이트하세요?',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 16),
        
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: _regions.map((region) {
            final isSelected = _selectedRegion == region.code;
            
            return SelectableChip(
              label: region.name,
              isSelected: isSelected,
              onTap: () => _onRegionSelected(region.code),
              icon: region.icon,
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildTransportMethodSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.directions, color: Theme.of(context).primaryColor),
            const SizedBox(width: 8),
            Text(
              '주로 어떻게 이동하시나요?',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 8),
        
        Text(
          '여러 개 선택 가능합니다',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        
        const SizedBox(height: 16),
        
        Column(
          children: TransportMethod.values.map((method) {
            final isSelected = _selectedTransportMethods.contains(method);
            
            return TransportMethodTile(
              method: method,
              isSelected: isSelected,
              onTap: () => _onTransportMethodToggled(method),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildInterestSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.favorite, color: Theme.of(context).primaryColor),
            const SizedBox(width: 8),
            Text(
              '어떤 곳을 좋아하시나요?',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 8),
        
        Text(
          '별점으로 관심도를 표현해주세요',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        
        const SizedBox(height: 16),
        
        Column(
          children: InterestCategory.values.map((category) {
            return InterestRatingTile(
              category: category,
              rating: _interestRatings[category] ?? 3,
              onRatingChanged: (rating) => _onInterestRatingChanged(category, rating),
            );
          }).toList(),
        ),
      ],
    );
  }

  void _onRegionSelected(String regionCode) {
    setState(() {
      _selectedRegion = regionCode;
    });
    
    _updatePreferences();
  }

  void _onTransportMethodToggled(TransportMethod method) {
    setState(() {
      if (_selectedTransportMethods.contains(method)) {
        _selectedTransportMethods.remove(method);
      } else {
        _selectedTransportMethods.add(method);
      }
    });
    
    _updatePreferences();
  }

  void _onInterestRatingChanged(InterestCategory category, int rating) {
    setState(() {
      _interestRatings[category] = rating;
    });
    
    _updatePreferences();
  }

  void _updatePreferences() {
    final controller = ref.read(onboardingControllerProvider.notifier);
    final currentPreferences = ref.read(onboardingControllerProvider).preferences;
    
    controller.updatePreferences(
      currentPreferences.copyWith(
        region: _selectedRegion,
        transportMethods: _selectedTransportMethods,
        interests: _interestRatings,
      ),
    );
  }
}

// 선택 가능한 칩 위젯
class SelectableChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final IconData? icon;

  const SelectableChip({
    Key? key,
    required this.label,
    required this.isSelected,
    required this.onTap,
    this.icon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? Theme.of(context).primaryColor : Colors.grey[100],
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: isSelected ? Theme.of(context).primaryColor : Colors.grey[300]!,
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                size: 18,
                color: isSelected ? Colors.white : Colors.grey[600],
              ),
              const SizedBox(width: 6),
            ],
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.grey[800],
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// 관심도 평가 위젯
class InterestRatingTile extends StatelessWidget {
  final InterestCategory category;
  final int rating;
  final ValueChanged<int> onRatingChanged;

  const InterestRatingTile({
    Key? key,
    required this.category,
    required this.rating,
    required this.onRatingChanged,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: category.color.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              category.icon,
              color: category.color,
              size: 20,
            ),
          ),
          
          const SizedBox(width: 16),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  category.displayName,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  category.description,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(width: 16),
          
          // 별점 선택
          Row(
            children: List.generate(5, (index) {
              final starIndex = index + 1;
              final isSelected = starIndex <= rating;
              
              return GestureDetector(
                onTap: () => onRatingChanged(starIndex),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: Icon(
                    isSelected ? Icons.star : Icons.star_border,
                    color: isSelected ? Colors.amber : Colors.grey[400],
                    size: 24,
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
```

---

## 4. 첫 체험 시스템

### 4-1. 체험 시나리오 관리
```dart
class FirstExperienceController {
  final ApiService _apiService;
  final AnalyticsService _analytics;
  
  FirstExperienceController(this._apiService, this._analytics);

  Future<void> startDemoExperience() async {
    // 데모 시나리오 시작
    await _analytics.trackEvent('demo_experience_started');
    
    // 예시 링크 준비
    const demoLink = "https://www.instagram.com/p/demo123/";
    const expectedResult = DemoAnalysisResult(
      placeName: "카페 VIBE",
      address: "서울 마포구 홍익로 12-34",
      category: ["카페", "디저트"],
      features: ["루프탑", "인스타 감성", "야외 테라스"],
      confidence: 0.95,
    );
    
    // 단계별 체험 실행
    await _runDemoSteps(demoLink, expectedResult);
  }

  Future<void> _runDemoSteps(String demoLink, DemoAnalysisResult expectedResult) async {
    // 1단계: 링크 분석 시뮬레이션
    await _simulateLinkAnalysis(demoLink, expectedResult);
    
    // 2단계: 장소 저장 체험
    await _simulatePlaceSaving(expectedResult);
    
    // 3단계: 코스 생성 체험
    await _simulateCourseCreation(expectedResult);
    
    // 4단계: 완료 축하
    await _showCompletionCelebration();
  }

  Future<void> _simulateLinkAnalysis(String link, DemoAnalysisResult result) async {
    // UI에서 링크 입력 애니메이션
    await Future.delayed(Duration(milliseconds: 500));
    
    // 분석 중 로딩 표시 (1-2초)
    await _showAnalysisLoading();
    
    // 결과 카드 애니메이션으로 등장
    await _showAnalysisResult(result);
    
    await _analytics.trackEvent('demo_analysis_completed');
  }

  Future<void> _simulatePlaceSaving(DemoAnalysisResult result) async {
    // 저장 버튼 하이라이트
    await _highlightSaveButton();
    
    // 사용자 액션 대기 또는 자동 진행
    await _waitForUserActionOrTimeout(
      action: 'save_place',
      timeout: Duration(seconds: 5),
    );
    
    // 위시리스트 추가 애니메이션
    await _showSaveAnimation();
    
    await _analytics.trackEvent('demo_place_saved');
  }

  Future<void> _simulateCourseCreation(DemoAnalysisResult result) async {
    // 추천 장소들을 보여줌
    final recommendedPlaces = await _getRecommendedPlaces(result);
    
    // "코스 만들기" 제안
    await _showCourseCreationSuggestion(recommendedPlaces);
    
    // 자동으로 코스 생성 (또는 사용자 확인 후)
    final demoRoute = await _generateDemoCourse(result, recommendedPlaces);
    
    // 지도에 경로 표시 애니메이션
    await _showRouteVisualization(demoRoute);
    
    await _analytics.trackEvent('demo_course_created');
  }

  Future<void> _showCompletionCelebration() async {
    // 축하 애니메이션 (파티클 효과)
    await _playConfettiAnimation();
    
    // 성과 요약 표시
    await _showAchievementSummary();
    
    // 다음 단계 안내
    await _showNextStepsGuidance();
    
    await _analytics.trackEvent('demo_experience_completed');
  }
}

// 데모 결과 모델
class DemoAnalysisResult {
  final String placeName;
  final String address;
  final List<String> category;
  final List<String> features;
  final double confidence;

  const DemoAnalysisResult({
    required this.placeName,
    required this.address,
    required this.category,
    required this.features,
    required this.confidence,
  });
}

// 첫 체험 UI
class FirstExperienceScreen extends StatefulWidget {
  const FirstExperienceScreen({Key? key}) : super(key: key);

  @override
  State<FirstExperienceScreen> createState() => _FirstExperienceScreenState();
}

class _FirstExperienceScreenState extends State<FirstExperienceScreen>
    with TickerProviderStateMixin {
  late AnimationController _typewriterController;
  late Animation<double> _typewriterAnimation;
  
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  
  ExperienceStep _currentStep = ExperienceStep.introduction;
  String _currentText = '';
  
  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _startExperience();
  }

  void _setupAnimations() {
    _typewriterController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _typewriterAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _typewriterController,
      curve: Curves.easeInOut,
    ));

    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _pulseAnimation = Tween<double>(
      begin: 0.9,
      end: 1.1,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 진행 표시
              LinearProgressIndicator(
                value: _getProgressForStep(_currentStep),
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).primaryColor,
                ),
              ),
              
              const SizedBox(height: 32),
              
              // 메인 콘텐츠
              Expanded(
                child: _buildStepContent(),
              ),
              
              // 하단 액션
              _buildBottomActions(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStepContent() {
    switch (_currentStep) {
      case ExperienceStep.introduction:
        return _buildIntroduction();
      case ExperienceStep.linkAnalysis:
        return _buildLinkAnalysisDemo();
      case ExperienceStep.placeSaving:
        return _buildPlaceSavingDemo();
      case ExperienceStep.courseCreation:
        return _buildCourseCreationDemo();
      case ExperienceStep.completion:
        return _buildCompletionCelebration();
    }
  }

  Widget _buildIntroduction() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '첫 체험해보기',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        
        const SizedBox(height: 16),
        
        Text(
          '인스타그램 링크 하나로 어떻게 데이트 코스가 만들어지는지 체험해보세요!',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: Colors.grey[600],
            height: 1.5,
          ),
        ),
        
        const SizedBox(height: 32),
        
        // 예시 링크 카드
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Theme.of(context).primaryColor.withOpacity(0.1),
                Theme.of(context).primaryColor.withOpacity(0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: Theme.of(context).primaryColor.withOpacity(0.3),
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.link,
                  color: Colors.white,
                ),
              ),
              
              const SizedBox(width: 16),
              
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '예시 링크',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: Theme.of(context).primaryColor,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    
                    const SizedBox(height: 4),
                    
                    Text(
                      'instagram.com/p/hongdae_cafe',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey[600],
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              ),
              
              Icon(
                Icons.arrow_forward_ios,
                color: Theme.of(context).primaryColor,
                size: 16,
              ),
            ],
          ),
        ),
        
        const Spacer(),
        
        // 시작 버튼
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _startDemo,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text(
              '체험 시작하기',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
        
        const SizedBox(height: 12),
        
        // 건너뛰기 옵션
        Center(
          child: TextButton(
            onPressed: _skipToRealUsage,
            child: Text(
              '체험 건너뛰고 바로 시작하기',
              style: TextStyle(
                color: Colors.grey[600],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLinkAnalysisDemo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'AI가 링크를 분석 중이에요',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        
        const SizedBox(height: 16),
        
        // 분석 과정 시각화
        _buildAnalysisVisualization(),
        
        const SizedBox(height: 32),
        
        // 결과 카드 (애니메이션으로 등장)
        if (_currentStep == ExperienceStep.linkAnalysis)
          _buildAnalysisResultCard(),
      ],
    );
  }
  
  Widget _buildAnalysisVisualization() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          // 링크 아이콘과 화살표
          Row(
            children: [
              _buildAnimatedIcon(Icons.link, Colors.blue),
              _buildArrow(),
              _buildAnimatedIcon(Icons.psychology, Colors.purple),
              _buildArrow(),
              _buildAnimatedIcon(Icons.place, Colors.green),
            ],
          ),
          
          const SizedBox(height: 24),
          
          // 진행 상황 텍스트
          AnimatedBuilder(
            animation: _typewriterAnimation,
            builder: (context, child) {
              final fullText = "링크 내용 분석 중... 장소 정보 추출 중... 완료!";
              final displayLength = (fullText.length * _typewriterAnimation.value).round();
              
              return Text(
                fullText.substring(0, displayLength),
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontFamily: 'monospace',
                  color: Colors.grey[700],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
```

---

## 5. 로컬 데이터 관리

### 5-1. Hive 데이터베이스 스키마
```dart
// 온보딩 진행 상태 저장
@HiveType(typeId: 0)
class OnboardingProgress {
  @HiveField(0)
  final Map<String, bool> completedSteps;
  
  @HiveField(1)
  final Map<String, bool> skippedSteps;
  
  @HiveField(2)
  final DateTime lastUpdated;
  
  @HiveField(3)
  final bool isCompleted;

  const OnboardingProgress({
    required this.completedSteps,
    required this.skippedSteps,
    required this.lastUpdated,
    required this.isCompleted,
  });
}

// 사용자 선호도 저장
@HiveType(typeId: 1)
class UserPreferencesHive {
  @HiveField(0)
  final String? region;
  
  @HiveField(1)
  final List<String> transportMethods;
  
  @HiveField(2)
  final Map<String, int> interests;
  
  @HiveField(3)
  final Map<String, dynamic> notificationSettings;
  
  @HiveField(4)
  final String theme;
  
  @HiveField(5)
  final DateTime createdAt;
  
  @HiveField(6)
  final DateTime updatedAt;

  const UserPreferencesHive({
    this.region,
    required this.transportMethods,
    required this.interests,
    required this.notificationSettings,
    required this.theme,
    required this.createdAt,
    required this.updatedAt,
  });
}

// 로컬 저장소 관리자
class OnboardingLocalStorage {
  static const String _onboardingBoxName = 'onboarding';
  static const String _preferencesBoxName = 'preferences';
  
  late Box<OnboardingProgress> _onboardingBox;
  late Box<UserPreferencesHive> _preferencesBox;

  Future<void> initialize() async {
    await Hive.initFlutter();
    
    // 어댑터 등록
    Hive.registerAdapter(OnboardingProgressAdapter());
    Hive.registerAdapter(UserPreferencesHiveAdapter());
    
    // 박스 열기
    _onboardingBox = await Hive.openBox<OnboardingProgress>(_onboardingBoxName);
    _preferencesBox = await Hive.openBox<UserPreferencesHive>(_preferencesBoxName);
  }

  Future<void> saveOnboardingProgress(OnboardingProgress progress) async {
    await _onboardingBox.put('current', progress);
  }

  OnboardingProgress? getOnboardingProgress() {
    return _onboardingBox.get('current');
  }

  Future<void> saveUserPreferences(UserPreferencesHive preferences) async {
    await _preferencesBox.put('current', preferences);
  }

  UserPreferencesHive? getUserPreferences() {
    return _preferencesBox.get('current');
  }

  Future<void> markOnboardingCompleted() async {
    final current = getOnboardingProgress();
    if (current != null) {
      final updated = OnboardingProgress(
        completedSteps: current.completedSteps,
        skippedSteps: current.skippedSteps,
        lastUpdated: DateTime.now(),
        isCompleted: true,
      );
      await saveOnboardingProgress(updated);
    }
  }

  bool isOnboardingCompleted() {
    final progress = getOnboardingProgress();
    return progress?.isCompleted ?? false;
  }

  Future<void> clearAllData() async {
    await _onboardingBox.clear();
    await _preferencesBox.clear();
  }
}
```

---

## 6. A/B 테스트 시스템

### 6-1. A/B 테스트 프레임워크
```dart
class OnboardingABTestManager {
  final FirebaseRemoteConfig _remoteConfig;
  final AnalyticsService _analytics;
  
  OnboardingABTestManager(this._remoteConfig, this._analytics);

  Future<void> initialize() async {
    await _remoteConfig.setDefaults({
      'onboarding_intro_screens': 3,
      'onboarding_experience_type': 'demo_link',
      'onboarding_setup_order': 'region_first',
      'onboarding_completion_reward': 'text_celebration',
    });

    await _remoteConfig.fetchAndActivate();
  }

  OnboardingVariant getCurrentVariant() {
    return OnboardingVariant(
      introScreenCount: _remoteConfig.getInt('onboarding_intro_screens'),
      experienceType: ExperienceType.values.firstWhere(
        (type) => type.name == _remoteConfig.getString('onboarding_experience_type'),
        orElse: () => ExperienceType.demoLink,
      ),
      setupOrder: SetupOrder.values.firstWhere(
        (order) => order.name == _remoteConfig.getString('onboarding_setup_order'),
        orElse: () => SetupOrder.regionFirst,
      ),
      completionReward: CompletionReward.values.firstWhere(
        (reward) => reward.name == _remoteConfig.getString('onboarding_completion_reward'),
        orElse: () => CompletionReward.textCelebration,
      ),
    );
  }

  Future<void> trackVariantExposure(OnboardingVariant variant) async {
    await _analytics.trackEvent('onboarding_variant_exposure', parameters: {
      'intro_screen_count': variant.introScreenCount,
      'experience_type': variant.experienceType.name,
      'setup_order': variant.setupOrder.name,
      'completion_reward': variant.completionReward.name,
    });
  }

  Future<void> trackVariantOutcome(
    OnboardingVariant variant, 
    OnboardingOutcome outcome,
  ) async {
    await _analytics.trackEvent('onboarding_variant_outcome', parameters: {
      'intro_screen_count': variant.introScreenCount,
      'experience_type': variant.experienceType.name,
      'setup_order': variant.setupOrder.name,
      'completion_reward': variant.completionReward.name,
      'outcome': outcome.name,
      'completion_time_seconds': outcome.completionTimeSeconds,
      'steps_skipped': outcome.stepsSkipped,
      'd1_retention': outcome.d1Retention,
      'd7_retention': outcome.d7Retention,
    });
  }
}

// A/B 테스트 모델
class OnboardingVariant {
  final int introScreenCount;
  final ExperienceType experienceType;
  final SetupOrder setupOrder;
  final CompletionReward completionReward;

  const OnboardingVariant({
    required this.introScreenCount,
    required this.experienceType,
    required this.setupOrder,
    required this.completionReward,
  });
}

enum ExperienceType {
  demoLink,
  popularCourses,
  interactiveWalkthrough,
}

enum SetupOrder {
  regionFirst,
  interestsFirst,
  transportFirst,
}

enum CompletionReward {
  textCelebration,
  firstCourseGift,
  achievementBadge,
  personalizedRecommendations,
}

class OnboardingOutcome {
  final String name;
  final int completionTimeSeconds;
  final int stepsSkipped;
  final bool d1Retention;
  final bool d7Retention;

  const OnboardingOutcome({
    required this.name,
    required this.completionTimeSeconds,
    required this.stepsSkipped,
    required this.d1Retention,
    required this.d7Retention,
  });
}
```

---

## 7. 성능 최적화

### 7-1. 이미지 및 리소스 최적화
```dart
class OnboardingResourceManager {
  static const Map<String, String> _preloadImages = {
    'welcome_bg': 'assets/onboarding/welcome_bg.webp',
    'feature_intro_1': 'assets/onboarding/feature_1.webp',
    'feature_intro_2': 'assets/onboarding/feature_2.webp',
    'feature_intro_3': 'assets/onboarding/feature_3.webp',
    'completion_celebration': 'assets/onboarding/celebration.webp',
  };

  static const Map<String, String> _animationAssets = {
    'link_analysis': 'assets/animations/link_analysis.json',
    'course_creation': 'assets/animations/course_creation.json',
    'completion_confetti': 'assets/animations/confetti.json',
  };

  Future<void> preloadResources() async {
    // 이미지 프리로딩
    final imagePreloadTasks = _preloadImages.entries.map((entry) async {
      try {
        await precacheImage(AssetImage(entry.value), Get.context!);
      } catch (e) {
        print('Failed to preload image ${entry.key}: $e');
      }
    });

    // 애니메이션 프리로딩
    final animationPreloadTasks = _animationAssets.entries.map((entry) async {
      try {
        await rootBundle.load(entry.value);
      } catch (e) {
        print('Failed to preload animation ${entry.key}: $e');
      }
    });

    await Future.wait([
      ...imagePreloadTasks,
      ...animationPreloadTasks,
    ]);
  }

  Future<void> cleanupUnusedResources() async {
    // 사용하지 않는 리소스 정리
    PaintingBinding.instance.imageCache.clear();
    
    // 메모리 정리
    await System.gc();
  }
}

// 메모리 효율적인 이미지 위젯
class OptimizedImage extends StatelessWidget {
  final String assetPath;
  final double? width;
  final double? height;
  final BoxFit fit;

  const OptimizedImage({
    Key? key,
    required this.assetPath,
    this.width,
    this.height,
    this.fit = BoxFit.contain,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      assetPath,
      width: width,
      height: height,
      fit: fit,
      cacheWidth: width?.round(),
      cacheHeight: height?.round(),
      errorBuilder: (context, error, stackTrace) {
        return Container(
          width: width,
          height: height,
          color: Colors.grey[200],
          child: Icon(
            Icons.image_not_supported,
            color: Colors.grey[400],
          ),
        );
      },
    );
  }
}
```

---

## 8. 분석 및 모니터링

### 8-1. 온보딩 분석 시스템
```dart
class OnboardingAnalytics {
  final FirebaseAnalytics _analytics;
  final CustomAnalyticsCollector _customAnalytics;
  
  OnboardingAnalytics(this._analytics, this._customAnalytics);

  Future<void> trackOnboardingStarted() async {
    final startTime = DateTime.now().millisecondsSinceEpoch;
    
    await Future.wait([
      _analytics.logEvent(name: 'onboarding_started'),
      _customAnalytics.trackEvent('onboarding_flow', {
        'action': 'started',
        'timestamp': startTime,
        'user_type': 'new',
      }),
    ]);
    
    // 시작 시간 저장 (완료 시간 계산용)
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('onboarding_start_time', startTime);
  }

  Future<void> trackStepCompleted(OnboardingStep step, Duration timeSpent) async {
    await Future.wait([
      _analytics.logEvent(
        name: 'onboarding_step_completed',
        parameters: {
          'step_name': step.name,
          'step_number': OnboardingStep.values.indexOf(step) + 1,
          'time_spent_seconds': timeSpent.inSeconds,
        },
      ),
      _customAnalytics.trackEvent('onboarding_step', {
        'step': step.name,
        'completed': true,
        'duration_ms': timeSpent.inMilliseconds,
      }),
    ]);
  }

  Future<void> trackStepSkipped(OnboardingStep step, String reason) async {
    await Future.wait([
      _analytics.logEvent(
        name: 'onboarding_step_skipped',
        parameters: {
          'step_name': step.name,
          'step_number': OnboardingStep.values.indexOf(step) + 1,
          'skip_reason': reason,
        },
      ),
      _customAnalytics.trackEvent('onboarding_step', {
        'step': step.name,
        'skipped': true,
        'reason': reason,
      }),
    ]);
  }

  Future<void> trackOnboardingCompleted(OnboardingCompletionData data) async {
    final prefs = await SharedPreferences.getInstance();
    final startTime = prefs.getInt('onboarding_start_time') ?? 0;
    final totalTime = DateTime.now().millisecondsSinceEpoch - startTime;
    
    await Future.wait([
      _analytics.logEvent(
        name: 'onboarding_completed',
        parameters: {
          'total_time_seconds': (totalTime / 1000).round(),
          'steps_completed': data.stepsCompleted,
          'steps_skipped': data.stepsSkipped,
          'preferences_set': data.preferencesSet,
        },
      ),
      _customAnalytics.trackEvent('onboarding_flow', {
        'action': 'completed',
        'total_duration_ms': totalTime,
        'completion_rate': data.completionRate,
        'user_preferences': data.preferences.toJson(),
      }),
    ]);
    
    // 완료 후 리텐션 추적 스케줄링
    await _scheduleRetentionTracking();
  }

  Future<void> trackOnboardingAbandoned(OnboardingStep lastStep, String reason) async {
    final prefs = await SharedPreferences.getInstance();
    final startTime = prefs.getInt('onboarding_start_time') ?? 0;
    final timeSpent = DateTime.now().millisecondsSinceEpoch - startTime;
    
    await Future.wait([
      _analytics.logEvent(
        name: 'onboarding_abandoned',
        parameters: {
          'last_step': lastStep.name,
          'abandon_reason': reason,
          'time_spent_seconds': (timeSpent / 1000).round(),
        },
      ),
      _customAnalytics.trackEvent('onboarding_flow', {
        'action': 'abandoned',
        'last_step': lastStep.name,
        'reason': reason,
        'duration_ms': timeSpent,
      }),
    ]);
  }

  Future<void> _scheduleRetentionTracking() async {
    // D1, D7 리텐션 추적을 위한 스케줄링
    final scheduler = NotificationScheduler();
    
    await scheduler.scheduleRetentionCheck(
      checkDate: DateTime.now().add(Duration(days: 1)),
      type: 'D1',
    );
    
    await scheduler.scheduleRetentionCheck(
      checkDate: DateTime.now().add(Duration(days: 7)),
      type: 'D7',
    );
  }
}

class OnboardingCompletionData {
  final int stepsCompleted;
  final int stepsSkipped;
  final bool preferencesSet;
  final double completionRate;
  final UserPreferences preferences;

  const OnboardingCompletionData({
    required this.stepsCompleted,
    required this.stepsSkipped,
    required this.preferencesSet,
    required this.completionRate,
    required this.preferences,
  });
}
```

---

## 9. 테스트 전략

### 9-1. 단위 테스트 (TDD)
```dart
class TestOnboardingController {
  @test
  void testOnboardingStateTransitions() {
    // Given
    final controller = OnboardingController();
    
    // When & Then - 초기 상태 확인
    expect(controller.state.currentStep, OnboardingStep.welcome);
    expect(controller.state.progress, 0.0);
    expect(controller.state.canSkip, true);
  }

  @test
  void testNextStepProgression() async {
    // Given
    final controller = OnboardingController();
    
    // When
    await controller.nextStep();
    
    // Then
    expect(controller.state.currentStep, OnboardingStep.featureIntro);
    expect(controller.state.completedSteps[OnboardingStep.welcome], true);
    expect(controller.state.progress, greaterThan(0.0));
  }

  @test
  void testSkipStepFunctionality() async {
    // Given
    final controller = OnboardingController();
    
    // When
    await controller.skipStep();
    
    // Then
    expect(controller.state.currentStep, OnboardingStep.featureIntro);
    expect(controller.state.skippedSteps[OnboardingStep.welcome], true);
    expect(controller.state.completedSteps[OnboardingStep.welcome], isNull);
  }

  @test
  void testPreferencesUpdate() async {
    // Given
    final controller = OnboardingController();
    final preferences = UserPreferences(
      region: 'seoul',
      transportMethods: [TransportMethod.walking],
      interests: {InterestCategory.cafe: 5},
    );
    
    // When
    await controller.updatePreferences(preferences);
    
    // Then
    expect(controller.state.preferences.region, 'seoul');
    expect(controller.state.preferences.transportMethods, contains(TransportMethod.walking));
    expect(controller.state.preferences.interests[InterestCategory.cafe], 5);
  }

  @test
  void testOnboardingCompletion() async {
    // Given
    final controller = OnboardingController();
    final localStorage = MockOnboardingLocalStorage();
    
    // When
    await controller.completeOnboarding();
    
    // Then
    verify(localStorage.markOnboardingCompleted()).called(1);
    verify(analytics.trackOnboardingCompleted(any)).called(1);
  }
}

class TestFirstExperienceController {
  @test
  void testDemoExperienceFlow() async {
    // Given
    final controller = FirstExperienceController(mockApiService, mockAnalytics);
    
    // When
    await controller.startDemoExperience();
    
    // Then
    verify(mockAnalytics.trackEvent('demo_experience_started')).called(1);
    verify(mockAnalytics.trackEvent('demo_analysis_completed')).called(1);
    verify(mockAnalytics.trackEvent('demo_place_saved')).called(1);
    verify(mockAnalytics.trackEvent('demo_course_created')).called(1);
  }
}
```

### 9-2. 위젯 테스트
```dart
class TestOnboardingWidgets {
  @testWidgets('OnboardingScreen should display progress correctly')
  Future<void> testOnboardingProgressDisplay(WidgetTester tester) async {
    // Given
    final mockState = OnboardingState(
      currentStep: OnboardingStep.basicSetup,
      totalSteps: 6,
      completedSteps: {
        OnboardingStep.welcome: true,
        OnboardingStep.featureIntro: true,
      },
      skippedSteps: {},
      preferences: UserPreferences(),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: ProviderScope(
          overrides: [
            onboardingControllerProvider.overrideWith((ref) => mockState),
          ],
          child: OnboardingScreen(),
        ),
      ),
    );

    // Then
    expect(find.byType(OnboardingProgressBar), findsOneWidget);
    
    final progressBar = tester.widget<OnboardingProgressBar>(
      find.byType(OnboardingProgressBar),
    );
    
    expect(progressBar.progress, closeTo(0.33, 0.01)); // 2/6 완료
    expect(progressBar.currentStep, OnboardingStep.basicSetup);
  }

  @testWidgets('BasicSetupScreen should handle user interactions')
  Future<void> testBasicSetupInteractions(WidgetTester tester) async {
    // Given
    await tester.pumpWidget(
      MaterialApp(
        home: ProviderScope(
          child: BasicSetupScreen(),
        ),
      ),
    );

    // When - 지역 선택
    await tester.tap(find.text('서울'));
    await tester.pump();

    // Then
    final selectedChip = tester.widget<SelectableChip>(
      find.widgetWithText(SelectableChip, '서울'),
    );
    expect(selectedChip.isSelected, true);
  }

  @testWidgets('Should show skip confirmation dialog')
  Future<void> testSkipConfirmationDialog(WidgetTester tester) async {
    // Given
    await tester.pumpWidget(
      MaterialApp(
        home: ProviderScope(
          child: OnboardingScreen(),
        ),
      ),
    );

    // When
    await tester.tap(find.text('나중에'));
    await tester.pump();

    // Then
    expect(find.byType(AlertDialog), findsOneWidget);
    expect(find.text('정말 건너뛰시겠어요?'), findsOneWidget);
  }
}
```

---

## 10. 용어 사전 (Technical)
- **State Machine:** 상태 전이를 관리하는 패턴
- **Progressive Setup:** 점진적으로 사용자 정보를 수집하는 방식
- **Preloading:** 리소스를 미리 로딩하여 성능을 향상시키는 기법
- **A/B Testing:** 두 가지 버전을 비교하여 더 나은 것을 선택하는 실험 방법
- **Retention:** 사용자가 앱을 계속 사용하는 비율
- **Onboarding Funnel:** 온보딩 과정에서 사용자 이탈률을 추적하는 분석 방법

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 06-onboarding-flow 버전과 연동