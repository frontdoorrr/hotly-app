# Task 6: UI/Frontend 개발 (UI & Frontend Development)

## 6-1. 디자인 시스템 및 컴포넌트 라이브러리 구축

### 목표
일관된 사용자 경험을 위한 재사용 가능한 컴포넌트 시스템 구축

### 사용자 가치
- **일관성**: 모든 화면에서 동일한 인터랙션 패턴으로 학습 비용 최소화
- **접근성**: WCAG 2.1 AA 준수로 모든 사용자가 이용 가능
- **개발 효율성**: 컴포넌트 재사용으로 개발 시간 50% 단축

### 가설 및 KPI
- **가설**: 체계적 디자인 시스템으로 UI 일관성 90% 향상, 개발 속도 50% 증가
- **측정 지표**:
  - 컴포넌트 재사용률 80% 이상
  - 접근성 준수율 100% (자동 테스트)
  - UI 개발 시간 대비 백엔드 개발 시간 비율 1:2

### 완료 정의 (DoD)
- [ ] Design Token 기반 스타일 시스템 구축
- [ ] Atomic Design 패턴으로 50+ 재사용 컴포넌트 구현
- [ ] Storybook 기반 컴포넌트 문서화 시스템
- [ ] 접근성 자동 테스트 (axe-core) 100% 통과
- [ ] 반응형 디자인 (모바일 우선, 태블릿/데스크톱 대응)

### 수용 기준
- Given 새로운 화면 개발, When 기존 컴포넌트 활용, Then 80% 이상 재사용으로 개발 완료
- Given 컴포넌트 변경, When Storybook 확인, Then 모든 변형 케이스 정상 동작
- Given 접근성 테스트 실행, When axe-core 검사, Then 모든 WCAG 2.1 AA 기준 통과

### 세부 작업

#### 6-1-1. Design Token 시스템 구축
**상세**: 색상, 타이포그래피, 간격, 그림자 등 디자인 요소 토큰화

**TDD 구현 순서**:
1. **RED**: Design Token 일관성 검증 테스트 작성
2. **GREEN**: CSS 변수 기반 토큰 시스템 구현
3. **REFACTOR**: 토큰 자동 검증 및 문서화 자동화

**구현 체크리스트**:
- [ ] Design Token 검증 테스트 작성 (`tests/test_design_tokens.ts`)
- [ ] 색상 팔레트 정의 (Primary, Semantic, Neutral)
- [ ] 타이포그래피 스케일 (Font Family, Size, Weight)
- [ ] 간격 시스템 (4px 기반 8배수 체계)
- [ ] 그림자/보더 시스템
- [ ] CSS Custom Properties 생성
- [ ] TypeScript 타입 정의
- [ ] 다크 모드 토큰 설정

**결과물**:
- `src/design-system/tokens.ts` - Design Token 정의
- `src/styles/tokens.css` - CSS 변수
- `src/types/design-tokens.ts` - TypeScript 타입
- `docs/design-tokens.md` - 토큰 문서

**성능 기준**:
- CSS 번들 크기 50KB 이하
- 토큰 변경 시 전체 빌드 30초 이내

**테스트**:
- 색상 대비 비율 검증 (4.5:1 이상)
- 타이포그래피 가독성 테스트
- 반응형 간격 시스템 검증

#### 6-1-2. Atomic 컴포넌트 구현 (Button, Input, Icon)
**상세**: 가장 기본적인 UI 요소들의 컴포넌트화

**TDD 구현 순서**:
1. **RED**: 각 컴포넌트 요구사항 테스트 작성
2. **GREEN**: 기본 기능 구현
3. **REFACTOR**: 접근성 및 성능 최적화

**구현 체크리스트**:
- [ ] Button 컴포넌트 테스트 작성 (`Button.test.tsx`)
- [ ] Button 컴포넌트 구현 (4가지 variant, 3가지 size)
- [ ] Input 컴포넌트 테스트 및 구현
- [ ] Icon 컴포넌트 시스템 (Heroicons + 커스텀)
- [ ] 접근성 속성 (ARIA labels, roles)
- [ ] 키보드 네비게이션 지원
- [ ] 포커스 관리 시스템

**결과물**:
- `src/components/atoms/Button/` - Button 컴포넌트
- `src/components/atoms/Input/` - Input 컴포넌트
- `src/components/atoms/Icon/` - Icon 시스템
- `src/hooks/useAccessibility.ts` - 접근성 훅

**성능 기준**:
- 컴포넌트 렌더링 16ms 이내 (60fps)
- 번들 크기 개별 컴포넌트 5KB 이하

**테스트**:
- 모든 props 조합 테스트
- 접근성 자동 테스트 (axe-core)
- 키보드 네비게이션 테스트

#### 6-1-3. Molecule 컴포넌트 구현 (SearchBar, PlaceCard)
**상세**: Atomic 컴포넌트를 조합한 복합 컴포넌트

**구현 체크리스트**:
- [ ] SearchBar 컴포넌트 테스트 및 구현
- [ ] PlaceCard 컴포넌트 (3가지 variant)
- [ ] FilterPanel 컴포넌트
- [ ] FormField 컴포넌트
- [ ] 상태 관리 및 이벤트 처리
- [ ] 로딩/에러 상태 표시

**결과물**:
- `src/components/molecules/SearchBar/`
- `src/components/molecules/PlaceCard/`
- `src/components/molecules/FilterPanel/`

#### 6-1-4. Storybook 설정 및 컴포넌트 문서화
**상세**: 컴포넌트 개발 환경 및 시각적 테스트 도구

**구현 체크리스트**:
- [ ] Storybook 7+ 설정
- [ ] 모든 컴포넌트 스토리 작성
- [ ] Controls addon 설정
- [ ] Accessibility addon 연동
- [ ] Visual regression 테스트

**결과물**:
- `.storybook/` - Storybook 설정
- `src/stories/` - 컴포넌트 스토리
- `docs/component-guide.md` - 사용 가이드

#### 6-1-5. 접근성 테스트 자동화
**상세**: WCAG 2.1 AA 준수를 위한 자동화된 접근성 검증

**구현 체크리스트**:
- [ ] axe-core 테스트 설정
- [ ] 스크린리더 테스트 자동화
- [ ] 키보드 네비게이션 테스트
- [ ] 색상 대비 자동 검증
- [ ] 터치 타겟 크기 검증

#### 6-1-6. 반응형 레이아웃 시스템
**상세**: 모바일 우선 반응형 디자인 시스템

**구현 체크리스트**:
- [ ] Breakpoint 시스템 정의
- [ ] Grid 시스템 구현
- [ ] 반응형 유틸리티 클래스
- [ ] 모바일/태블릿/데스크톱 레이아웃

---

## 6-2. 핵심 화면 UI 구현

### 목표
사용자 핵심 여정에 해당하는 주요 화면들의 UI 구현

### 완료 정의 (DoD)
- [ ] 홈 화면 (장소 추천, 최근 활동)
- [ ] 검색 화면 (검색바, 필터, 결과 목록)
- [ ] 장소 상세 화면 (이미지, 정보, 액션)
- [ ] 코스 생성/편집 화면 (드래그 앤 드롭)
- [ ] 프로필 화면 (설정, 저장된 장소/코스)

### 세부 작업

#### 6-2-1. 홈 화면 구현
**상세**: 개인화 추천, 최근 활동, 빠른 액세스

**구현 체크리스트**:
- [ ] 홈 화면 테스트 작성
- [ ] 개인화 추천 섹션
- [ ] 최근 활동 타임라인
- [ ] 빠른 액세스 버튼
- [ ] 알림 배너 영역

**컴포넌트 구성**:
```typescript
<HomeScreen>
  <TopAppBar title="Hotly" actions={[notifications, search]} />
  <ScrollableContainer onRefresh={refreshData}>
    <RecommendationSection places={recommended} />
    <QuickActions actions={[searchPlace, createCourse]} />
    <RecentActivity activities={recent} />
    <PopularPlaces places={popular} />
  </ScrollableContainer>
  <BottomNavigationBar currentTab="home" />
</HomeScreen>
```

#### 6-2-2. 검색 화면 구현
**상세**: 통합 검색, 고급 필터, 결과 표시

**구현 체크리스트**:
- [ ] 검색 화면 테스트 작성
- [ ] 통합 검색바 구현
- [ ] 실시간 자동완성
- [ ] 고급 필터 패널
- [ ] 검색 결과 목록/지도 뷰

**컴포넌트 구성**:
```typescript
<SearchScreen>
  <SearchHeader>
    <SearchBar onSearch={search} suggestions={suggestions} />
    <FilterButton onPress={openFilter} activeCount={filterCount} />
  </SearchHeader>
  <SearchResults>
    <ViewToggle mode={viewMode} onChange={setViewMode} />
    {viewMode === 'list' ?
      <PlaceList places={results} /> :
      <MapView places={results} />
    }
  </SearchResults>
  <FilterModal isOpen={showFilter} filters={filters} />
</SearchScreen>
```

#### 6-2-3. 장소 상세 화면 구현
**상세**: 장소 정보 표시, 액션 버튼, 리뷰/평점

**구현 체크리스트**:
- [ ] 장소 상세 화면 테스트
- [ ] 이미지 갤러리 구현
- [ ] 장소 정보 표시
- [ ] 액션 버튼 (저장, 공유, 경로)
- [ ] 리뷰 및 평점 시스템

**컴포넌트 구성**:
```typescript
<PlaceDetailScreen>
  <PlaceImageGallery images={place.images} />
  <PlaceInfo place={place} />
  <ActionButtons>
    <LikeButton liked={isLiked} onToggle={toggleLike} />
    <SaveButton saved={isSaved} onToggle={toggleSave} />
    <ShareButton onShare={sharePlae} />
    <DirectionsButton onPress={openDirections} />
  </ActionButtons>
  <ReviewSection reviews={reviews} />
</PlaceDetailScreen>
```

#### 6-2-4. 코스 생성/편집 화면 구현
**상세**: 드래그 앤 드롭 인터페이스, 경로 시각화

**구현 체크리스트**:
- [ ] 코스 편집 화면 테스트
- [ ] 드래그 앤 드롭 리스트
- [ ] 장소 추가/제거 기능
- [ ] 경로 미리보기
- [ ] 소요시간/거리 계산

**컴포넌트 구성**:
```typescript
<CourseBuilderScreen>
  <CourseHeader>
    <Input placeholder="코스 제목" />
    <CourseTypeSelector types={courseTypes} />
  </CourseHeader>
  <CourseTimeline>
    <DragDropList
      items={places}
      onReorder={reorderPlaces}
      renderItem={({ place, index }) => (
        <CoursePlace
          place={place}
          order={index + 1}
          onRemove={() => removePlace(place.id)}
        />
      )}
    />
  </CourseTimeline>
  <AddPlaceButton onPress={openPlaceSearch} />
  <CourseActions>
    <Button variant="outline" onPress={previewCourse}>미리보기</Button>
    <Button variant="primary" onPress={saveCourse}>저장</Button>
  </CourseActions>
</CourseBuilderScreen>
```

#### 6-2-5. 프로필 화면 구현
**상세**: 사용자 정보, 설정, 저장된 컨텐츠 관리

**구현 체크리스트**:
- [ ] 프로필 화면 테스트
- [ ] 사용자 정보 표시/편집
- [ ] 설정 메뉴 구현
- [ ] 저장된 장소/코스 목록
- [ ] 통계 및 인사이트

**컴포넌트 구성**:
```typescript
<ProfileScreen>
  <ProfileHeader>
    <Avatar src={user.avatar} size="lg" />
    <UserInfo user={user} />
    <StatsRow stats={userStats} />
  </ProfileHeader>
  <ProfileTabs>
    <TabPanel label="저장된 장소">
      <PlaceList places={savedPlaces} />
    </TabPanel>
    <TabPanel label="내 코스">
      <CourseList courses={myCourses} />
    </TabPanel>
    <TabPanel label="설정">
      <SettingsMenu items={settingsItems} />
    </TabPanel>
  </ProfileTabs>
</ProfileScreen>
```

---

## 6-3. 인터랙션 및 애니메이션 시스템

### 목표
자연스럽고 직관적인 사용자 인터랙션 경험 제공

### 완료 정의 (DoD)
- [ ] 제스처 기반 인터랙션 (스와이프, 드래그, 핀치)
- [ ] 마이크로 애니메이션 시스템 (60fps 보장)
- [ ] 햅틱 피드백 연동
- [ ] 로딩 상태 애니메이션

### 세부 작업

#### 6-3-1. 제스처 인터랙션 구현
**상세**: 스와이프, 드래그, 핀치 제스처 처리

**구현 체크리스트**:
- [ ] 제스처 인터랙션 테스트
- [ ] 스와이프 제스처 (좌/우/상/하)
- [ ] 드래그 앤 드롭 시스템
- [ ] 핀치 줌 (지도 화면)
- [ ] 제스처 충돌 방지

**컴포넌트**:
```typescript
<SwipeableRecommendation
  places={recommendations}
  onSwipeLeft={dislike}
  onSwipeRight={like}
  onSwipeUp={save}
/>

<DragDropCourseBuilder
  places={coursePlaces}
  onReorder={reorderPlaces}
/>
```

#### 6-3-2. 애니메이션 시스템 구현
**상세**: 자연스러운 전환 애니메이션, 마이크로 인터랙션

**구현 체크리스트**:
- [ ] 애니메이션 라이브러리 선택 (Framer Motion)
- [ ] 화면 전환 애니메이션
- [ ] 리스트 아이템 애니메이션
- [ ] 로딩 애니메이션
- [ ] 성공/실패 피드백 애니메이션

**성능 기준**:
- 애니메이션 프레임률 60fps 유지
- 애니메이션 지연 시간 16ms 이하

#### 6-3-3. 햅틱 피드백 시스템
**상세**: 터치 피드백으로 사용자 경험 향상

**구현 체크리스트**:
- [ ] 햅틱 피드백 훅 구현
- [ ] 액션별 피드백 패턴 정의
- [ ] 설정 기반 on/off 제어
- [ ] 플랫폼별 대응 (iOS/Android)

---

## 6-4. 상태 관리 및 데이터 플로우

### 목표
효율적인 상태 관리와 데이터 플로우로 일관된 사용자 경험 제공

### 완료 정의 (DoD)
- [ ] 전역 상태 관리 시스템 (Zustand/Redux Toolkit)
- [ ] API 데이터 캐싱 및 동기화 (React Query)
- [ ] 오프라인 지원 (Service Worker)
- [ ] 실시간 업데이트 (WebSocket)

### 세부 작업

#### 6-4-1. 전역 상태 관리 시스템
**상세**: 사용자 정보, 앱 설정, UI 상태 관리

**구현 체크리스트**:
- [ ] 상태 관리 라이브러리 선택 및 설정
- [ ] 사용자 상태 스토어
- [ ] 앱 설정 상태 스토어
- [ ] UI 상태 스토어 (모달, 로딩 등)
- [ ] 상태 영속화 (localStorage)

**상태 구조**:
```typescript
interface AppState {
  user: UserState;
  places: PlacesState;
  courses: CoursesState;
  ui: UIState;
  settings: SettingsState;
}
```

#### 6-4-2. API 데이터 캐싱 및 동기화
**상세**: 서버 상태 관리, 캐싱 전략, 옵티미스틱 업데이트

**구현 체크리스트**:
- [ ] React Query 설정
- [ ] API 캐싱 전략 구현
- [ ] 옵티미스틱 업데이트
- [ ] 백그라운드 동기화
- [ ] 오프라인 큐 시스템

#### 6-4-3. 실시간 업데이트 시스템
**상세**: WebSocket 기반 실시간 데이터 동기화

**구임 체크리스트**:
- [ ] WebSocket 연결 관리
- [ ] 실시간 이벤트 처리
- [ ] 연결 상태 관리
- [ ] 재연결 로직
- [ ] 이벤트 큐잉 시스템

---

## 6-5. 성능 최적화

### 목표
60fps 버터 스무스 UI와 빠른 로딩 시간 달성

### 완료 정의 (DoD)
- [ ] 초기 로딩 시간 3초 이내
- [ ] 화면 전환 애니메이션 60fps 보장
- [ ] 메모리 사용량 최적화 (50MB 이하)
- [ ] 번들 크기 최적화 (초기 로드 500KB 이하)

### 세부 작업

#### 6-5-1. 번들 최적화 및 코드 스플리팅
**구현 체크리스트**:
- [ ] 라우트 기반 코드 스플리팅
- [ ] 컴포넌트 지연 로딩
- [ ] 트리 셰이킹 최적화
- [ ] 중복 의존성 제거

#### 6-5-2. 이미지 및 자산 최적화
**구현 체크리스트**:
- [ ] 이미지 지연 로딩
- [ ] WebP 포맷 지원
- [ ] 이미지 압축 자동화
- [ ] CDN 연동

#### 6-5-3. 렌더링 성능 최적화
**구현 체크리스트**:
- [ ] React.memo 적용
- [ ] 가상화 스크롤 (긴 목록)
- [ ] 불필요한 리렌더링 방지
- [ ] 메모리 누수 방지

---

## 6-6. UI 테스트 시스템

### 목표
안정적이고 신뢰할 수 있는 UI 테스트 자동화

### 완료 정의 (DoD)
- [ ] 컴포넌트 단위 테스트 80% 커버리지
- [ ] E2E 테스트 주요 사용자 플로우 100% 커버
- [ ] 시각적 회귀 테스트 자동화
- [ ] 접근성 테스트 자동화

### 세부 작업

#### 6-6-1. 컴포넌트 테스트 작성
**TDD 적용**:
```typescript
// 1. RED: 실패하는 테스트 작성
describe('PlaceCard', () => {
  it('should_display_place_name_when_place_provided', () => {
    const place = { name: '카페 이름', category: 'cafe' };
    render(<PlaceCard place={place} />);
    expect(screen.getByText('카페 이름')).toBeInTheDocument();
  });
});

// 2. GREEN: 테스트 통과하는 최소 구현
const PlaceCard = ({ place }) => (
  <div>{place.name}</div>
);

// 3. REFACTOR: 완전한 구현으로 개선
const PlaceCard = ({ place, onLike, onSave }) => (
  <Card>
    <Image src={place.image} alt={place.name} />
    <CardContent>
      <Typography variant="h6">{place.name}</Typography>
      <Typography variant="body2">{place.category}</Typography>
    </CardContent>
    <CardActions>
      <LikeButton onPress={() => onLike(place.id)} />
      <SaveButton onPress={() => onSave(place.id)} />
    </CardActions>
  </Card>
);
```

#### 6-6-2. E2E 테스트 자동화
**주요 사용자 플로우**:
- 회원가입 → 온보딩 → 첫 장소 저장
- 링크 입력 → 분석 → 장소 추가 → 코스 생성
- 검색 → 필터 → 장소 선택 → 저장

#### 6-6-3. 시각적 회귀 테스트
**구현 체크리스트**:
- [ ] Chromatic 또는 Percy 설정
- [ ] 컴포넌트별 스냅샷 생성
- [ ] 반응형 스냅샷 테스트
- [ ] 테마별 스냅샷 (라이트/다크)

---

## 참고 문서
- `ui-design-system.md` - 디자인 시스템 가이드
- `prd/` - 각 기능별 UI 요구사항
- `rules.md` - 코드 품질 및 테스트 가이드라인

---

*작성일: 2025-01-XX*
*작성자: Claude*
*버전: 1.0*
