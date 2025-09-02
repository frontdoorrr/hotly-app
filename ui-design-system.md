# Hotly App - UI Design System & Component Guidelines

## 1. Design System Overview

### 1.1 Design Principles
- **사용자 중심**: 3초 내 핵심 액션 접근 가능
- **일관성**: 모든 화면에서 동일한 패턴 적용
- **접근성**: WCAG 2.1 AA 준수, 최소 터치 44dp
- **반응형**: 다양한 화면 크기 대응

### 1.2 Component Architecture
- **Atomic Design**: Atoms → Molecules → Organisms → Templates → Pages
- **재사용성**: 80% 이상 컴포넌트 재사용률 목표
- **일관성**: Design Token 기반 스타일 통일

---

## 2. Design Tokens

### 2.1 Color Palette
```typescript
// Primary Colors
const colors = {
  primary: {
    50: '#FFF5F5',
    100: '#FED7D7', 
    500: '#E53E3E', // Main brand color
    600: '#C53030',
    900: '#742A2A'
  },
  
  // Semantic Colors
  success: '#38A169',
  warning: '#D69E2E', 
  error: '#E53E3E',
  info: '#3182CE',
  
  // Neutral Colors
  gray: {
    50: '#F7FAFC',
    100: '#EDF2F7',
    200: '#E2E8F0',
    500: '#A0ADB8',
    700: '#2D3748',
    900: '#1A202C'
  }
};
```

### 2.2 Typography Scale
```typescript
const typography = {
  fontFamily: {
    primary: 'Pretendard, -apple-system, sans-serif',
    monospace: 'JetBrains Mono, monospace'
  },
  
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px  
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem' // 30px
  },
  
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  }
};
```

### 2.3 Spacing System
```typescript
const spacing = {
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem'     // 64px
};
```

### 2.4 Border Radius
```typescript
const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px  
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px'
};
```

---

## 3. Atomic Components

### 3.1 Atoms (최소 단위)

#### Button Component
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
  onClick?: () => void;
}

// 사용 예시
<Button variant="primary" size="md" loading={isSubmitting}>
  장소 저장
</Button>
```

#### Input Component
```typescript
interface InputProps {
  type: 'text' | 'email' | 'password' | 'search';
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

// 사용 예시
<Input 
  type="search"
  placeholder="장소나 주소를 검색하세요"
  value={searchQuery}
  onChange={setSearchQuery}
  leftIcon={<SearchIcon />}
/>
```

#### Icon Component
```typescript
interface IconProps {
  name: IconName;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  className?: string;
}

// 아이콘 라이브러리: Heroicons + 커스텀 아이콘
const iconMap = {
  search: SearchIcon,
  heart: HeartIcon,
  map: MapIcon,
  share: ShareIcon,
  // ... 50+ 아이콘
};
```

### 3.2 Form Elements

#### FormField Component
```typescript
interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  helpText?: string;
  children: ReactNode;
}

// 사용 예시
<FormField label="장소명" required error={errors.name}>
  <Input value={name} onChange={setName} />
</FormField>
```

#### Select Component
```typescript
interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  multiple?: boolean;
}

// 사용 예시
<Select 
  options={categoryOptions}
  value={selectedCategory}
  onChange={setSelectedCategory}
  placeholder="카테고리 선택"
  searchable
/>
```

---

## 4. Molecules (조합 컴포넌트)

### 4.1 Search Components

#### SearchBar Component
```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  onFilter: () => void;
  suggestions?: string[];
  loading?: boolean;
  recent?: string[];
}

// 내부 구성: Input + Button + AutoComplete
<SearchBar 
  onSearch={handleSearch}
  onFilter={openFilterModal}
  suggestions={searchSuggestions}
  recent={recentSearches}
/>
```

#### FilterPanel Component
```typescript
interface FilterPanelProps {
  filters: FilterConfig[];
  values: FilterValues;
  onChange: (values: FilterValues) => void;
  onReset: () => void;
  onApply: () => void;
}

// 내부 구성: FormField + Select + Slider + Checkbox
<FilterPanel 
  filters={availableFilters}
  values={currentFilters}
  onChange={setFilters}
/>
```

### 4.2 Place Components

#### PlaceCard Component
```typescript
interface PlaceCardProps {
  place: Place;
  onLike: (id: string) => void;
  onSave: (id: string) => void;
  onShare: (id: string) => void;
  variant: 'list' | 'grid' | 'minimal';
}

// 내부 구성: Image + Text + ActionButtons
<PlaceCard 
  place={place}
  onLike={handleLike}
  variant="grid"
/>
```

#### PlaceDetail Component
```typescript
interface PlaceDetailProps {
  place: Place;
  reviews?: Review[];
  onAddToCourse: () => void;
  onNavigate: () => void;
}

// 내부 구성: Gallery + Info + Actions + Reviews
<PlaceDetail 
  place={selectedPlace}
  reviews={placeReviews}
  onAddToCourse={addToCurrentCourse}
/>
```

---

## 5. Organisms (복합 컴포넌트)

### 5.1 Navigation Components

#### BottomNavigationBar
```typescript
interface BottomNavProps {
  currentTab: TabName;
  onTabChange: (tab: TabName) => void;
  badgeCount?: Record<TabName, number>;
}

const tabs = [
  { name: 'home', icon: 'home', label: '홈' },
  { name: 'search', icon: 'search', label: '검색' },
  { name: 'courses', icon: 'map', label: '코스' },
  { name: 'profile', icon: 'user', label: '프로필' }
];
```

#### TopAppBar
```typescript
interface TopAppBarProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
  actions?: AppBarAction[];
  transparent?: boolean;
}

// 사용 예시
<TopAppBar 
  title="장소 검색"
  showBack
  actions={[
    { icon: 'filter', onPress: openFilter },
    { icon: 'more', onPress: openMenu }
  ]}
/>
```

### 5.2 List Components

#### PlaceList Component
```typescript
interface PlaceListProps {
  places: Place[];
  loading?: boolean;
  onLoadMore?: () => void;
  onPlaceSelect: (place: Place) => void;
  variant: 'list' | 'grid';
  emptyState?: ReactNode;
}

// 내부 구성: PlaceCard[] + LoadingSpinner + EmptyState
<PlaceList 
  places={searchResults}
  loading={isLoading}
  onLoadMore={loadNextPage}
  variant="grid"
/>
```

#### CourseTimeline Component
```typescript
interface CourseTimelineProps {
  places: CoursePlace[];
  onReorder: (places: CoursePlace[]) => void;
  onRemove: (id: string) => void;
  editable?: boolean;
}

// 내부 구성: DraggableList + TimeBadge + DistanceBadge
<CourseTimeline 
  places={coursePlaces}
  onReorder={handleReorder}
  editable={isEditing}
/>
```

---

## 6. Layout Components

### 6.1 Screen Templates

#### MainLayout
```typescript
interface MainLayoutProps {
  children: ReactNode;
  showBottomNav?: boolean;
  showTopBar?: boolean;
  backgroundType?: 'default' | 'map' | 'gradient';
}

<MainLayout showBottomNav showTopBar>
  <ScreenContent />
</MainLayout>
```

#### ModalLayout
```typescript
interface ModalLayoutProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'full';
  children: ReactNode;
}

<ModalLayout 
  isOpen={showPlaceDetail}
  onClose={closePlaceDetail}
  title="장소 상세정보"
  size="lg"
>
  <PlaceDetail place={selectedPlace} />
</ModalLayout>
```

### 6.2 Container Components

#### ContentContainer
```typescript
interface ContentContainerProps {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: ReactNode;
}
```

#### ScrollableContainer
```typescript
interface ScrollableContainerProps {
  onRefresh?: () => Promise<void>;
  onLoadMore?: () => void;
  loading?: boolean;
  children: ReactNode;
}
```

---

## 7. Screen-Specific Components

### 7.1 Onboarding Screens

#### OnboardingStep Component
```typescript
interface OnboardingStepProps {
  step: number;
  totalSteps: number;
  title: string;
  description: string;
  children: ReactNode;
  onNext?: () => void;
  onSkip?: () => void;
  nextLabel?: string;
}

<OnboardingStep 
  step={1}
  totalSteps={5}
  title="관심사를 선택해주세요"
  description="취향에 맞는 장소를 추천해드려요"
  onNext={handleNext}
>
  <InterestSelector />
</OnboardingStep>
```

#### ProgressIndicator Component
```typescript
interface ProgressIndicatorProps {
  current: number;
  total: number;
  variant: 'dots' | 'bar' | 'steps';
}
```

### 7.2 Map Components

#### MapView Component
```typescript
interface MapViewProps {
  places: Place[];
  courses?: Course[];
  center?: LatLng;
  zoom?: number;
  onPlaceSelect: (place: Place) => void;
  onMapMove?: (center: LatLng, zoom: number) => void;
  clustering?: boolean;
}

<MapView 
  places={nearbyPlaces}
  center={currentLocation}
  onPlaceSelect={selectPlace}
  clustering
/>
```

#### MapMarker Component
```typescript
interface MapMarkerProps {
  place: Place;
  selected?: boolean;
  clustered?: boolean;
  onClick: () => void;
}
```

#### MapControls Component
```typescript
interface MapControlsProps {
  onCurrentLocation: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onMapType: () => void;
}
```

### 7.3 Course Components

#### CourseBuilder Component
```typescript
interface CourseBuilderProps {
  places: Place[];
  onAddPlace: (place: Place) => void;
  onRemovePlace: (id: string) => void;
  onReorderPlaces: (places: Place[]) => void;
  onSaveCourse: (course: Course) => void;
}

// 내부 구성: DragDropList + AddPlaceButton + CourseSettings
<CourseBuilder 
  places={selectedPlaces}
  onAddPlace={addPlace}
  onSaveCourse={saveCourse}
/>
```

#### CoursePreview Component
```typescript
interface CoursePreviewProps {
  course: Course;
  onEdit?: () => void;
  onShare?: () => void;
  onStart?: () => void;
  editable?: boolean;
}
```

---

## 8. Interactive Components

### 8.1 Gesture Components

#### SwipeableCard Component
```typescript
interface SwipeableCardProps {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  children: ReactNode;
  disabled?: boolean;
}

// 사용 예시: 장소 추천 카드
<SwipeableCard 
  onSwipeLeft={rejectPlace}
  onSwipeRight={likePlace}
  onSwipeUp={savePlace}
>
  <PlaceCard place={recommendedPlace} />
</SwipeableCard>
```

#### DragDropList Component
```typescript
interface DragDropListProps {
  items: DragDropItem[];
  onReorder: (items: DragDropItem[]) => void;
  renderItem: (item: DragDropItem) => ReactNode;
  disabled?: boolean;
}
```

### 8.2 Animation Components

#### FadeInView Component
```typescript
interface FadeInViewProps {
  delay?: number;
  duration?: number;
  children: ReactNode;
}
```

#### SlideInPanel Component
```typescript
interface SlideInPanelProps {
  isOpen: boolean;
  direction: 'up' | 'down' | 'left' | 'right';
  onClose: () => void;
  children: ReactNode;
}
```

---

## 9. State Management Components

### 9.1 Data Loading States

#### LoadingSpinner Component
```typescript
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  text?: string;
}
```

#### SkeletonLoader Component
```typescript
interface SkeletonLoaderProps {
  type: 'text' | 'image' | 'card' | 'list';
  count?: number;
  animated?: boolean;
}

// 사용 예시
<SkeletonLoader type="card" count={3} animated />
```

#### EmptyState Component
```typescript
interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onPress: () => void;
  };
}

<EmptyState 
  icon={<SearchIcon />}
  title="검색 결과가 없어요"
  description="다른 키워드로 검색해보세요"
  action={{
    label: "인기 장소 보기",
    onPress: showPopularPlaces
  }}
/>
```

### 9.2 Error Handling Components

#### ErrorBoundary Component
```typescript
interface ErrorBoundaryProps {
  fallback?: ReactNode;
  onError?: (error: Error) => void;
  children: ReactNode;
}
```

#### ErrorAlert Component
```typescript
interface ErrorAlertProps {
  error: AppError;
  onRetry?: () => void;
  onDismiss?: () => void;
  severity: 'error' | 'warning' | 'info';
}
```

---

## 10. Specialized Components

### 10.1 Link Analysis Components

#### LinkInputCard Component
```typescript
interface LinkInputCardProps {
  onSubmit: (url: string) => void;
  loading?: boolean;
  supportedPlatforms: Platform[];
}

<LinkInputCard 
  onSubmit={analyzeLik}
  loading={isAnalyzing}
  supportedPlatforms={['instagram', 'youtube', 'blog']}
/>
```

#### AnalysisResult Component
```typescript
interface AnalysisResultProps {
  result: AnalysisResult;
  onAddPlace: (place: ExtractedPlace) => void;
  onReanalyze: () => void;
}
```

### 10.2 Social Components

#### LikeButton Component
```typescript
interface LikeButtonProps {
  liked: boolean;
  count: number;
  onToggle: () => void;
  size?: 'sm' | 'md';
  animated?: boolean;
}
```

#### ShareButton Component
```typescript
interface ShareButtonProps {
  shareData: ShareData;
  platforms: SharePlatform[];
  onShare: (platform: SharePlatform) => void;
}
```

#### CommentList Component
```typescript
interface CommentListProps {
  comments: Comment[];
  onAddComment: (content: string) => void;
  onLikeComment: (id: string) => void;
  onReportComment: (id: string) => void;
}
```

---

## 11. Component Development Guidelines

### 11.1 TDD for Components
```typescript
// 1. RED: 테스트 먼저 작성
describe('Button Component', () => {
  it('should_render_primary_variant_when_variant_is_primary', () => {
    render(<Button variant="primary">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');
  });
  
  it('should_call_onClick_when_button_is_clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

// 2. GREEN: 최소 구현
const Button = ({ variant, children, onClick }) => {
  return (
    <button 
      className={`btn btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

// 3. REFACTOR: 개선 및 최적화
const Button = memo(({ variant, children, onClick, ...props }) => {
  const className = useMemo(() => 
    clsx('btn', `btn-${variant}`, props.className), 
    [variant, props.className]
  );
  
  return <button className={className} onClick={onClick} {...props} />;
});
```

### 11.2 Component Testing Strategy
- **단위 테스트**: 모든 props 조합, 이벤트 핸들러
- **접근성 테스트**: 스크린리더, 키보드 네비게이션
- **시각적 회귀 테스트**: Storybook 기반 스냅샷
- **사용성 테스트**: 터치 타겟 크기, 제스처 응답

### 11.3 Performance Guidelines
- **메모이제이션**: React.memo, useMemo, useCallback 적극 활용
- **지연 로딩**: React.lazy, 이미지 lazy loading
- **번들 최적화**: 트리 셰이킹, 코드 스플리팅
- **렌더링 최적화**: key props, 불필요한 리렌더링 방지

---

## 12. Storybook Integration

### 12.1 Component Stories
```typescript
// Button.stories.tsx
export default {
  title: 'Atoms/Button',
  component: Button,
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'outline', 'ghost']
    }
  }
};

export const Primary = {
  args: {
    variant: 'primary',
    children: '버튼 텍스트'
  }
};

export const WithIcon = {
  args: {
    variant: 'primary',
    icon: <HeartIcon />,
    children: '좋아요'
  }
};
```

### 12.2 Design Token Stories
- **Colors**: 모든 컬러 팔레트 시각화
- **Typography**: 폰트 크기별 샘플 텍스트
- **Spacing**: 여백 시스템 가이드
- **Icons**: 전체 아이콘 라이브러리

---

## 13. Accessibility Guidelines

### 13.1 Required Standards
- **WCAG 2.1 AA** 준수
- **최소 터치 타겟**: 44dp × 44dp
- **색상 대비**: 4.5:1 이상 (일반 텍스트), 3:1 이상 (대형 텍스트)
- **스크린리더**: 모든 인터랙티브 요소에 적절한 레이블

### 13.2 Implementation
```typescript
// 접근성 훅 예시
const useAccessibility = () => ({
  announceToScreenReader: (message: string) => {
    // 스크린리더 알림
  },
  
  getFocusableElements: (container: HTMLElement) => {
    // 포커스 가능한 요소 반환
  },
  
  trapFocus: (container: HTMLElement) => {
    // 포커스 트랩 구현
  }
});
```

### 13.3 Testing
- **자동화 도구**: axe-core, react-axe
- **수동 테스트**: 스크린리더, 키보드 네비게이션
- **색상 대비**: 디자인 토큰 자동 검증

---

## 14. Responsive Design

### 14.1 Breakpoints
```typescript
const breakpoints = {
  sm: '640px',   // 모바일
  md: '768px',   // 태블릿 세로
  lg: '1024px',  // 태블릿 가로
  xl: '1280px',  // 데스크톱
  '2xl': '1536px' // 대형 데스크톱
};
```

### 14.2 Responsive Components
```typescript
// 반응형 그리드 시스템
interface GridProps {
  cols: ResponsiveValue<number>;
  gap: ResponsiveValue<number>;
  children: ReactNode;
}

<Grid cols={{ sm: 1, md: 2, lg: 3 }} gap={{ sm: 4, md: 6 }}>
  {places.map(place => <PlaceCard key={place.id} place={place} />)}
</Grid>
```

---

## 15. Component Documentation

### 15.1 PropTypes & TypeScript
- **모든 컴포넌트**: TypeScript 인터페이스 정의 필수
- **JSDoc**: 복잡한 props에 대한 상세 설명
- **기본값**: defaultProps 또는 ES6 기본 매개변수

### 15.2 Usage Examples
- **Storybook**: 모든 컴포넌트 스토리 작성
- **README**: 컴포넌트별 사용법 문서
- **Live Examples**: 실제 화면에서 사용 예시

---

## 16. Implementation Tasks

### Phase 1: Foundation (1주)
- [ ] Design Token 정의 및 CSS 변수 설정
- [ ] Atomic 컴포넌트 구현 (Button, Input, Icon)
- [ ] Storybook 설정 및 기본 스토리

### Phase 2: Molecules (1주)  
- [ ] Form 컴포넌트 구현 (SearchBar, FilterPanel)
- [ ] Place 관련 컴포넌트 (PlaceCard, PlaceDetail)
- [ ] 접근성 테스트 자동화

### Phase 3: Organisms (1주)
- [ ] Navigation 컴포넌트 (BottomNav, TopAppBar)
- [ ] List 컴포넌트 (PlaceList, CourseTimeline)
- [ ] 반응형 레이아웃 구현

### Phase 4: Integration (1주)
- [ ] 화면별 특화 컴포넌트
- [ ] 성능 최적화 및 번들 사이즈 검증
- [ ] 전체 디자인 시스템 문서화

---

*작성일: 2025-01-XX*  
*작성자: Claude*  
*버전: 1.0*