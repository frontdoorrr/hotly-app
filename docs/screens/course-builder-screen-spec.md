# 코스 생성 화면 스펙 (Course Builder Screen Specification)

## 문서 정보
- **화면명**: 코스 생성/편집 화면 (Course Builder Screen)
- **라우트**: `/courses/create`, `/courses/:courseId/edit`
- **버전**: 1.0
- **작성일**: 2025-01-XX

---

## 1. 화면 목적

- 여러 장소를 조합하여 데이트/여행 코스 생성
- 드래그 앤 드롭으로 순서 조정
- 이동 경로 및 소요 시간 자동 계산

---

## 2. 와이어프레임

```
┌─────────────────────────────────────┐
│  ← 코스 만들기           [미리보기]  │ ← App Bar
├─────────────────────────────────────┤
│  코스 제목                          │
│  ┌─────────────────────────────┐   │ ← Title Input
│  │ 강남 데이트 코스            │   │
│  └─────────────────────────────┘   │
│                                     │
│  코스 타입                          │
│  [데이트] [여행] [맛집투어] [기타]  │ ← Type Chips
│                                     │
│  ──────────────────────────────────│
│                                     │
│  장소 (3)             총 5.5시간    │ ← Timeline Header
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ≡  1. 카페 A       [삭제]   │   │ ← Draggable Item
│  │    10:00 - 11:30 (1.5h)     │   │
│  │    ┌─────────────────┐      │   │
│  │    │ 체류시간: [1.5h]│      │   │   (Expanded)
│  │    └─────────────────┘      │   │
│  └─────────────────────────────┘   │
│         ↓ 도보 10분, 800m          │
│  ┌─────────────────────────────┐   │
│  │ ≡  2. 레스토랑 B    [삭제]  │   │
│  │    12:00 - 13:30 (1.5h)     │   │
│  └─────────────────────────────┘   │
│         ↓ 차량 15분, 3.2km         │
│  ┌─────────────────────────────┐   │
│  │ ≡  3. 전망대 C      [삭제]  │   │
│  │    14:00 - 16:00 (2h)       │   │
│  └─────────────────────────────┘   │
│                                     │
│  [➕ 장소 추가하기]                │ ← Add Button
│                                     │
└─────────────────────────────────────┘
│  [취소]              [저장하기]     │ ← Bottom Actions
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리

```dart
CourseBuilderScreen (ConsumerStatefulWidget)
└─ Scaffold
   ├─ AppBar
   │  ├─ Leading: BackButton
   │  ├─ Title: "코스 만들기"
   │  └─ Actions: [PreviewButton]
   │
   ├─ Body: CustomScrollView
   │  └─ SliverList
   │     ├─ CourseFormSection
   │     │  ├─ TitleTextField
   │     │  └─ TypeChips
   │     │
   │     ├─ TimelineHeader (장소 개수, 총 시간)
   │     │
   │     └─ ReorderableListView (드래그 앤 드롭)
   │        ├─ CoursePlaceCard (체류 시간 조정)
   │        ├─ RouteInfoCard (이동 정보)
   │        ├─ CoursePlaceCard
   │        └─ ...
   │
   ├─ FloatingActionButton
   │  └─ "장소 추가하기"
   │
   └─ BottomAppBar
      └─ Row: [CancelButton, SaveButton]
```

---

## 4. 핵심 컴포넌트

### 4.1 드래그 앤 드롭 리스트

```dart
class CoursePlacesList extends ConsumerWidget {
  final List<CoursePlace> places;
  final Function(int oldIndex, int newIndex) onReorder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ReorderableListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: places.length * 2 - 1, // 장소 + 경로 정보
      onReorder: onReorder,
      itemBuilder: (context, index) {
        if (index.isOdd) {
          // 경로 정보 (드래그 불가)
          return RouteInfoCard(
            key: ValueKey('route_${index ~/ 2}'),
            from: places[index ~/ 2],
            to: places[index ~/ 2 + 1],
          );
        }

        // 장소 카드 (드래그 가능)
        final placeIndex = index ~/ 2;
        return CoursePlaceCard(
          key: ValueKey('place_${places[placeIndex].id}'),
          place: places[placeIndex],
          order: placeIndex + 1,
          onDurationChanged: (duration) {
            ref.read(courseBuilderProvider.notifier)
                .updateDuration(placeIndex, duration);
          },
          onDelete: () {
            ref.read(courseBuilderProvider.notifier)
                .removePlace(placeIndex);
          },
        );
      },
    );
  }
}
```

### 4.2 CoursePlaceCard

```dart
class CoursePlaceCard extends StatefulWidget {
  final CoursePlace place;
  final int order;
  final Function(Duration) onDurationChanged;
  final VoidCallback onDelete;

  @override
  State<CoursePlaceCard> createState() => _CoursePlaceCardState();
}

class _CoursePlaceCardState extends State<CoursePlaceCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        children: [
          ListTile(
            leading: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.drag_handle), // 드래그 핸들
                const SizedBox(width: 8),
                CircleAvatar(
                  child: Text('${widget.order}'),
                ),
              ],
            ),
            title: Text(widget.place.name),
            subtitle: Text(
              '${_formatTime(widget.place.startTime)} - '
              '${_formatTime(widget.place.endTime)} '
              '(${widget.place.duration.inMinutes}분)',
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: Icon(_isExpanded
                    ? Icons.expand_less
                    : Icons.expand_more),
                  onPressed: () {
                    setState(() => _isExpanded = !_isExpanded);
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: widget.onDelete,
                ),
              ],
            ),
          ),

          // 체류 시간 조정 (확장 시 표시)
          if (_isExpanded)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('체류 시간'),
                  Slider(
                    value: widget.place.duration.inMinutes.toDouble(),
                    min: 30,
                    max: 240,
                    divisions: 14,
                    label: '${widget.place.duration.inMinutes}분',
                    onChanged: (value) {
                      widget.onDurationChanged(
                        Duration(minutes: value.toInt()),
                      );
                    },
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:'
           '${time.minute.toString().padLeft(2, '0')}';
  }
}
```

---

## 5. 상태 관리

```dart
final courseBuilderProvider = StateNotifierProvider.autoDispose<
    CourseBuilderNotifier, CourseBuilderState>((ref) {
  return CourseBuilderNotifier();
});

class CourseBuilderNotifier extends StateNotifier<CourseBuilderState> {
  CourseBuilderNotifier() : super(CourseBuilderState.initial());

  void addPlace(Place place) {
    final newPlace = CoursePlace.fromPlace(
      place,
      order: state.places.length + 1,
      startTime: _calculateStartTime(),
      duration: const Duration(hours: 1),
    );

    state = state.copyWith(
      places: [...state.places, newPlace],
    );

    _recalculateRoute();
  }

  void removePlace(int index) {
    final updatedPlaces = List<CoursePlace>.from(state.places);
    updatedPlaces.removeAt(index);

    state = state.copyWith(places: updatedPlaces);
    _recalculateRoute();
  }

  void reorderPlaces(int oldIndex, int newIndex) {
    final updatedPlaces = List<CoursePlace>.from(state.places);
    final place = updatedPlaces.removeAt(oldIndex);
    updatedPlaces.insert(newIndex, place);

    state = state.copyWith(places: updatedPlaces);
    _recalculateRoute();
  }

  Future<void> _recalculateRoute() async {
    // 경로 및 소요 시간 재계산
    final totalDuration = state.places.fold<Duration>(
      Duration.zero,
      (sum, place) => sum + place.duration,
    );

    state = state.copyWith(totalDuration: totalDuration);
  }
}

@freezed
class CourseBuilderState with _$CourseBuilderState {
  const factory CourseBuilderState({
    required String title,
    required CourseType type,
    required List<CoursePlace> places,
    required Duration totalDuration,
  }) = _CourseBuilderState;

  factory CourseBuilderState.initial() => const CourseBuilderState(
    title: '',
    type: CourseType.date,
    places: [],
    totalDuration: Duration.zero,
  );
}
```

---

## 6. 완료 정의 (DoD)

- [ ] 코스 제목 및 타입 설정
- [ ] 장소 추가/삭제
- [ ] 드래그 앤 드롭 순서 변경 (햅틱 피드백)
- [ ] 체류 시간 조정
- [ ] 총 소요 시간 자동 계산
- [ ] 이동 경로 정보 표시
- [ ] 코스 저장 및 공유

---

## 8. 수용 기준

- **Given** 장소 3개 선택
- **When** 드래그하여 순서 변경
- **Then** 즉시 순서 업데이트, 총 시간 재계산, 햅틱 피드백

