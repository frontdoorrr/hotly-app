# 장소 상세 화면 스펙 (Place Detail Screen Specification)

## 문서 정보
- **화면명**: 장소 상세 화면 (Place Detail Screen)
- **라우트**: `/places/:placeId`
- **버전**: 1.0
- **작성일**: 2025-01-XX

---

## 1. 화면 목적

- 장소의 상세 정보 표시 (이미지, 위치, 설명, 리뷰)
- 장소 저장, 좋아요, 공유 기능
- 코스에 추가 및 경로 찾기

---

## 2. 와이어프레임

```
┌─────────────────────────────────────┐
│  ← 　　　　　　　　　　 ❤️ 공유 ⋮  │ ← Transparent AppBar
├─────────────────────────────────────┤
│  ┌─────────────────────────────────┐│
│  │    [이미지 갤러리 - 스와이프]   ││ ← Image Gallery
│  │         ● ○ ○ ○               ││   (PageView)
│  └─────────────────────────────────┘│
│                                     │
│  카페 A                   ⭐ 4.8   │ ← Place Info
│  #카페 #데이트 #뷰맛집             │
│                                     │
│  📍 서울시 강남구 테헤란로 123      │
│     [지도 보기]  [경로 찾기]       │
│                                     │
│  ──────────────────────────────────│
│                                     │
│  소개                               │ ← Description
│  분위기 좋은 루프탑 카페입니다...   │
│                                     │
│  영업시간                           │ ← Business Hours
│  매일 10:00 - 22:00                │
│                                     │
│  전화번호                           │
│  02-1234-5678     [전화걸기]       │
│                                     │
│  ──────────────────────────────────│
│                                     │
│  리뷰 (24)              [더보기 →] │ ← Reviews
│  ┌─────────────────────────────┐   │
│  │ 👤 김민지  ⭐⭐⭐⭐⭐       │   │
│  │ 분위기가 너무 좋아요!       │   │
│  │ 2일 전                      │   │
│  └─────────────────────────────┘   │
│                                     │
│  비슷한 장소                        │ ← Similar Places
│  [카드] [카드] [카드]              │
│                                     │
└─────────────────────────────────────┘
│  [💾 저장] [➕ 코스에 추가]        │ ← Bottom Actions
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리

```dart
PlaceDetailScreen (ConsumerWidget)
└─ Scaffold
   ├─ Body: CustomScrollView
   │  ├─ SliverAppBar (Expandable)
   │  │  ├─ FlexibleSpaceBar
   │  │  │  └─ ImageGallery (PageView)
   │  │  └─ Actions: [LikeButton, ShareButton, MoreButton]
   │  │
   │  ├─ SliverToBoxAdapter (장소 정보)
   │  │  └─ PlaceInfoSection
   │  │     ├─ PlaceName + Rating
   │  │     ├─ TagChips
   │  │     └─ AddressSection
   │  │
   │  ├─ SliverToBoxAdapter (설명)
   │  │  └─ DescriptionSection
   │  │
   │  ├─ SliverToBoxAdapter (영업시간/연락처)
   │  │  └─ ContactInfoSection
   │  │
   │  ├─ SliverToBoxAdapter (리뷰)
   │  │  └─ ReviewsSection
   │  │     └─ ReviewCard (최대 3개 미리보기)
   │  │
   │  └─ SliverGrid (비슷한 장소)
   │     └─ PlaceCard
   │
   └─ BottomAppBar
      └─ Row: [SaveButton, AddToCourseButton]
```

---

## 4. 핵심 컴포넌트

### 4.1 ImageGallery

```dart
class ImageGallery extends StatefulWidget {
  final List<String> imageUrls;

  const ImageGallery({Key? key, required this.imageUrls}) : super(key: key);

  @override
  State<ImageGallery> createState() => _ImageGalleryState();
}

class _ImageGalleryState extends State<ImageGallery> {
  int _currentPage = 0;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        PageView.builder(
          itemCount: widget.imageUrls.length,
          onPageChanged: (index) => setState(() => _currentPage = index),
          itemBuilder: (context, index) {
            return Hero(
              tag: 'place_image_${widget.imageUrls[index]}',
              child: CachedNetworkImage(
                imageUrl: widget.imageUrls[index],
                fit: BoxFit.cover,
                placeholder: (context, url) => const Center(
                  child: CircularProgressIndicator(),
                ),
              ),
            );
          },
        ),

        // Page Indicator
        Positioned(
          bottom: 16,
          left: 0,
          right: 0,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              widget.imageUrls.length,
              (index) => Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _currentPage == index
                      ? Colors.white
                      : Colors.white.withOpacity(0.5),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
```

### 4.2 PlaceInfoSection

```dart
class PlaceInfoSection extends StatelessWidget {
  final Place place;

  const PlaceInfoSection({Key? key, required this.place}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 장소명 + 평점
          Row(
            children: [
              Expanded(
                child: Text(
                  place.name,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ),
              if (place.rating != null) ...[
                const Icon(Icons.star, color: Colors.amber, size: 20),
                const SizedBox(width: 4),
                Text(
                  place.rating!.toStringAsFixed(1),
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ],
          ),

          const SizedBox(height: 12),

          // 태그
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: place.tags.map((tag) {
              return Chip(
                label: Text('#$tag'),
                visualDensity: VisualDensity.compact,
              );
            }).toList(),
          ),

          const SizedBox(height: 16),

          // 주소
          Row(
            children: [
              const Icon(Icons.location_on, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  place.address ?? '주소 정보 없음',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // 액션 버튼
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.map),
                  label: const Text('지도 보기'),
                  onPressed: () => _showMap(context, place),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.directions),
                  label: const Text('경로 찾기'),
                  onPressed: () => _openDirections(place),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showMap(BuildContext context, Place place) {
    // 지도 모달 표시
  }

  void _openDirections(Place place) {
    // 카카오맵/구글맵 앱 실행
  }
}
```

---

## 5. 상태 관리

```dart
// Providers
final placeDetailProvider = FutureProvider.autoDispose.family<Place, String>(
  (ref, placeId) async {
    final repository = ref.read(placeRepositoryProvider);
    final result = await repository.getPlaceById(placeId);

    return result.when(
      success: (place) => place,
      failure: (error) => throw Exception(error),
    );
  },
);

final placeReviewsProvider = FutureProvider.autoDispose.family<List<Review>, String>(
  (ref, placeId) async {
    final repository = ref.read(reviewRepositoryProvider);
    final result = await repository.getReviews(placeId, limit: 3);

    return result.when(
      success: (reviews) => reviews,
      failure: (_) => [],
    );
  },
);

// Like 토글
final toggleLikeProvider = FutureProvider.family<void, String>(
  (ref, placeId) async {
    final repository = ref.read(placeRepositoryProvider);
    await repository.toggleLike(placeId);

    // 장소 상세 다시 로드
    ref.invalidate(placeDetailProvider(placeId));
  },
);
```

---

## 6. API 연동

```dart
GET /api/v1/places/:placeId
GET /api/v1/places/:placeId/reviews?limit=3
POST /api/v1/places/:placeId/like
POST /api/v1/places/:placeId/save
```

---

## 7. 완료 정의 (DoD)

- [ ] 이미지 갤러리 스와이프 동작
- [ ] 장소 정보 표시 (이름, 평점, 주소, 태그)
- [ ] 좋아요, 저장, 공유 기능
- [ ] 리뷰 미리보기 (최대 3개)
- [ ] 비슷한 장소 추천
- [ ] 경로 찾기 (카카오맵/구글맵 연동)
- [ ] Hero 애니메이션 (이미지 전환)

---

## 8. 수용 기준

- **Given** 장소 카드 탭
- **When** 장소 상세 화면 이동
- **Then** 0.3초 이내 화면 전환, Hero 애니메이션 적용, 3초 이내 모든 정보 로드

