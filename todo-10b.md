# TODO: [10-b] Place 아카이브 → Map 통합

todo0424의 E 섹션 중 [11]만 먼저 처리함. [10-b]는 모델/백엔드 의존성이 있어 별도 이슈로 분리.

## 문제

- Map 탭은 `savedPlacesProvider` (`/api/v1/places`) 데이터만 사용
- Place 타입 아카이브는 `/api/v1/archive`에 저장되지만 Map에 반영 안 됨
- 사용자 관점: 장소를 아카이빙해도 지도에서 찾을 수 없음

## 현재 스키마 갭

`ArchivedContent` 엔티티:
- ✅ `typeSpecificData['address']` (문자열)
- ❌ `latitude` / `longitude` 없음
- ❌ Place ID로 매핑할 외래키 없음

Map이 요구하는 `Place` 엔티티:
- `latitude`, `longitude` (nullable이지만 마커 표시에 필수)
- `category`, `tags`

## 접근법 비교

### (A) 백엔드 통합 ⭐ 권장
- Archive 저장 시 backend가 place 타입이면 geocoding → Place 레코드 자동 생성
- Archive ↔ Place 를 ID로 연결
- 프론트는 수정 불필요 (기존 savedPlacesProvider가 그대로 동작)

**백엔드 작업**:
- `backend/app/services/place_analysis_service.py` 근처에서 archive 저장 후 Place 생성 훅
- geocoding 서비스 (카카오 Local API) 호출
- DB 마이그레이션: `archive_id` FK를 `places` 테이블에 추가 or 반대 방향
- 이미 저장된 place 아카이브를 소급 처리할 backfill job

### (B) 프론트 머지
- Map에서 archive API 별도 호출 → place 타입만 필터 → 주소 geocoding → 마커 추가
- 단점:
  - geocoding 왕복이 장소 수만큼 발생 (N+1)
  - 캐시/중복 관리 복잡
  - Archive 삭제 시 Map 동기화 직접 처리 필요
  - 저장/좋아요/태그 등 Place 기능과 연결 안 됨

### (C) 모델에 lat/lng 추가
- `ArchivedContent`에 `latitude`, `longitude`, `placeId` 추가
- Archive 저장 시 백엔드가 geocoding → 필드 채움
- 프론트가 lat/lng 있는 place 아카이브를 Map에 마커로 추가
- Place 저장 기능과는 여전히 분리

## [11] 구현 결과와의 호환성

[11]에서 `SearchResultInfo` 개선:
- 검색 결과(카카오 Local API에서 받은 즉석 데이터) 전용 위젯
- `PlaceSearchResult` 엔티티 사용 (lat/lng 필수)
- 저장 콜백(`onSave`)은 향후 "Map 검색 결과 → 저장" 플로우로 쓰일 수 있음

[10-b]가 구현될 때 **충돌 없음**:
- [10-b]가 (A)안이면: Place 레코드가 생기므로 기존 저장 플로우 그대로
- [10-b]가 (B)/(C)안이면: archive provider에서 파생된 Place를 Map 마커 리스트에 append

## 권장 다음 단계

1. 백엔드에서 archive place → Place 자동 생성 플로우 지원 여부 확인
2. 지원 안 되면 (A)안 백엔드 작업 티켓 오픈
3. 백엔드 작업이 길어지면 임시로 (B)안을 "베스트 에포트 마커" 수준으로 추가

## 관련 파일

- `frontend/lib/features/archive/domain/entities/archived_content.dart`
- `frontend/lib/features/map/presentation/providers/map_provider.dart`
- `frontend/lib/features/map/presentation/screens/map_screen.dart`
- `frontend/lib/features/saved/presentation/providers/saved_places_provider.dart`
- `frontend/lib/shared/models/place.dart`
- `backend/app/services/place_analysis_service.py`
- `backend/app/api/api_v1/endpoints/link_analysis.py`
