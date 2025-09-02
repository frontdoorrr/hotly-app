# TRD: 장소 저장, 태그, 위시리스트 관리

## 1. 기술 개요
**목적:** PRD 02-place-management 요구사항을 충족하기 위한 장소 데이터 관리, 분류, 검색 시스템 설계

**핵심 기술 스택:**
- Database: PostgreSQL (관계형 + JSONB)
- Search: PostgreSQL trigram + Elasticsearch (전문 검색)
- Cache: Redis (분산 캐싱)
- API: FastAPI + Pydantic
- ML: scikit-learn (자동 분류)

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Mobile App]
    ↓ CRUD Operations
[API Gateway]
    ↓
[Place Management Service]
    ├── [Classification Engine] (자동 카테고리)
    ├── [Tagging System] (사용자 태그)
    ├── [Duplicate Detector] (중복 방지)
    └── [State Manager] (상태 관리)
         ↓
[PostgreSQL] + [Elasticsearch] + [Redis Cache]
```

### 2-2. 마이크로서비스 분해
```
1. Place CRUD Service
   - 장소 생성/조회/수정/삭제
   - 상태 변경 (위시리스트→즐겨찾기→방문완료)
   - 메타데이터 관리

2. Classification Service
   - AI 기반 자동 카테고리 분류
   - 머신러닝 모델 학습/추론
   - 분류 신뢰도 계산

3. Tagging Service
   - 사용자 정의 태그 관리
   - 태그 자동완성/제안
   - 태그 통계 및 분석

4. Search & Filter Service
   - 복합 검색 (이름, 주소, 태그)
   - 필터링 및 정렬
   - 검색 결과 캐싱
```

---

## 3. 데이터베이스 설계

### 3-1. PostgreSQL 스키마
```sql
-- places 테이블
CREATE TABLE places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    place_id UUID NOT NULL DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    address TEXT NULL,
    coordinates POINT NULL, -- PostGIS 지원
    category VARCHAR(20) NOT NULL CHECK (category IN ('cafe', 'restaurant', 'tourist', 'shopping', 'culture', 'activity')),
    auto_category_confidence DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    user_tags TEXT[] NOT NULL DEFAULT '{}',
    system_tags TEXT[] NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'wishlist' CHECK (status IN ('wishlist', 'favorite', 'planned', 'visited')),
    rating DECIMAL(2,1) NULL CHECK (rating >= 1.0 AND rating <= 5.0),
    memo TEXT NULL,
    image_url TEXT NULL,
    business_hours TEXT NULL,
    price_range VARCHAR(20) NULL CHECK (price_range IN ('under_10k', '10k_20k', '20k_30k', '30k_50k', 'over_50k')),
    visit_count INTEGER NOT NULL DEFAULT 0,
    last_visited_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}',
    UNIQUE(user_id, place_id)
);

-- 인덱스 정의
CREATE INDEX idx_places_user_created ON places(user_id, created_at DESC);
CREATE INDEX idx_places_user_category ON places(user_id, category);
CREATE INDEX idx_places_user_status ON places(user_id, status);
CREATE INDEX idx_places_user_tags ON places USING GIN(user_tags);
CREATE INDEX idx_places_coordinates ON places USING GIST(coordinates); -- PostGIS 지리 검색
CREATE INDEX idx_places_search ON places USING GIN(to_tsvector('korean', name || ' ' || COALESCE(address, ''))); -- 전문 검색
CREATE INDEX idx_places_trigram ON places USING GIN(name gin_trgm_ops); -- trigram 유사도 검색

-- 사용자별 태그 통계 테이블
CREATE TABLE user_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tag VARCHAR(50) NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 1,
    last_used TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    category_distribution JSONB NOT NULL DEFAULT '{}',
    UNIQUE(user_id, tag)
);

CREATE INDEX idx_user_tags_user_usage ON user_tags(user_id, usage_count DESC);
CREATE INDEX idx_user_tags_tag ON user_tags USING GIN(tag gin_trgm_ops);

-- PostGIS 확장 및 trigram 확장 필요
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 3-2. Elasticsearch 인덱스
```json
{
  "mappings": {
    "properties": {
      "user_id": {"type": "keyword"},
      "place_id": {"type": "keyword"},
      "name": {
        "type": "text",
        "analyzer": "korean",
        "fields": {
          "keyword": {"type": "keyword"},
          "ngram": {
            "type": "text",
            "analyzer": "korean_ngram"
          }
        }
      },
      "address": {
        "type": "text", 
        "analyzer": "korean"
      },
      "category": {"type": "keyword"},
      "user_tags": {"type": "keyword"},
      "status": {"type": "keyword"},
      "rating": {"type": "float"},
      "location": {"type": "geo_point"},
      "created_at": {"type": "date"},
      "price_range": {"type": "keyword"}
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "korean": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["lowercase", "nori_part_of_speech"]
        },
        "korean_ngram": {
          "type": "custom", 
          "tokenizer": "nori_tokenizer",
          "filter": ["lowercase", "nori_part_of_speech", "edge_ngram"]
        }
      }
    }
  }
}
```

---

## 4. API 설계

### 4-1. Place CRUD APIs
```python
# Request/Response Models
class PlaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    category: Optional[PlaceCategory] = None
    user_tags: List[str] = Field(default_factory=list, max_items=10)
    memo: Optional[str] = Field(None, max_length=500)
    image_url: Optional[HttpUrl] = None
    price_range: Optional[PriceRange] = None

class PlaceResponse(BaseModel):
    place_id: str
    name: str
    address: Optional[str]
    coordinates: Optional[Coordinates]
    category: PlaceCategory
    auto_category_confidence: float
    user_tags: List[str]
    status: PlaceStatus
    rating: Optional[float]
    memo: Optional[str]
    created_at: datetime
    updated_at: datetime

# API 엔드포인트
@router.post("/places", response_model=PlaceResponse)
async def create_place(
    request: PlaceCreateRequest,
    current_user: User = Depends(get_current_user),
    place_service: PlaceService = Depends()
):
    # 중복 검사
    existing = await place_service.find_duplicate(current_user.id, request.name, request.address)
    if existing:
        raise HTTPException(409, "이미 저장된 장소입니다")
    
    # 자동 카테고리 분류
    if not request.category:
        request.category, confidence = await place_service.classify_place(request)
    
    place = await place_service.create_place(current_user.id, request)
    return PlaceResponse.from_orm(place)

@router.get("/places", response_model=List[PlaceResponse])
async def get_places(
    category: Optional[PlaceCategory] = None,
    status: Optional[PlaceStatus] = None,
    tags: Optional[List[str]] = Query(default=None),
    sort: PlaceSortBy = PlaceSortBy.CREATED_DESC,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    place_service: PlaceService = Depends()
):
    filters = PlaceFilters(
        category=category,
        status=status, 
        tags=tags,
        sort=sort
    )
    
    places = await place_service.get_places(
        current_user.id, 
        filters, 
        limit=limit, 
        offset=offset
    )
    
    return [PlaceResponse.from_orm(place) for place in places]
```

### 4-2. 태그 관리 APIs
```python
class TagSuggestionResponse(BaseModel):
    tag: str
    usage_count: int
    category_distribution: Dict[str, int]

@router.get("/tags/suggestions", response_model=List[TagSuggestionResponse])
async def get_tag_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends()
):
    suggestions = await tag_service.get_tag_suggestions(
        current_user.id, 
        query, 
        limit
    )
    return suggestions

@router.put("/places/{place_id}/tags")
async def update_place_tags(
    place_id: str,
    tags: List[str] = Body(..., max_items=10),
    current_user: User = Depends(get_current_user),
    place_service: PlaceService = Depends()
):
    # 태그 정규화
    normalized_tags = [tag_service.normalize_tag(tag) for tag in tags]
    
    updated_place = await place_service.update_tags(
        current_user.id,
        place_id, 
        normalized_tags
    )
    
    # 태그 사용 통계 업데이트
    await tag_service.update_tag_usage(current_user.id, normalized_tags)
    
    return PlaceResponse.from_orm(updated_place)
```

---

## 5. 자동 분류 시스템

### 5-1. 머신러닝 분류기
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

class PlaceClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words=self._load_korean_stopwords()
        )
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        self.categories = ['cafe', 'restaurant', 'tourist', 'shopping', 'culture', 'activity']
        self.model_version = "v1.0"
    
    def train(self, training_data: List[Tuple[str, str, str]]):
        """
        training_data: [(name, address, category), ...]
        """
        features = []
        labels = []
        
        for name, address, category in training_data:
            text = f"{name} {address or ''}"
            features.append(text)
            labels.append(category)
        
        # 특성 벡터화
        X = self.vectorizer.fit_transform(features)
        
        # 모델 학습
        self.classifier.fit(X, labels)
        
        # 모델 저장
        self.save_model()
    
    def predict(self, name: str, address: str = None) -> Tuple[str, float]:
        text = f"{name} {address or ''}"
        X = self.vectorizer.transform([text])
        
        # 예측 및 확률 계산
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        confidence = max(probabilities)
        
        return prediction, confidence
    
    def save_model(self):
        joblib.dump({
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'categories': self.categories,
            'version': self.model_version
        }, f'models/place_classifier_{self.model_version}.pkl')
    
    @classmethod
    def load_model(cls, model_path: str):
        model_data = joblib.load(model_path)
        instance = cls()
        instance.vectorizer = model_data['vectorizer']
        instance.classifier = model_data['classifier']
        instance.categories = model_data['categories']
        instance.model_version = model_data['version']
        return instance

# 분류 서비스
class ClassificationService:
    def __init__(self):
        self.classifier = PlaceClassifier.load_model('models/place_classifier_v1.0.pkl')
        self.min_confidence_threshold = 0.7
    
    async def classify_place(self, name: str, address: str = None) -> Tuple[str, float]:
        category, confidence = self.classifier.predict(name, address)
        
        # 신뢰도가 낮으면 기본값 사용
        if confidence < self.min_confidence_threshold:
            return 'restaurant', confidence  # 기본 카테고리
        
        return category, confidence
    
    async def batch_classify(self, places: List[Tuple[str, str]]) -> List[Tuple[str, float]]:
        results = []
        for name, address in places:
            category, confidence = await self.classify_place(name, address)
            results.append((category, confidence))
        return results
```

### 5-2. 온라인 학습 시스템
```python
class OnlineLearningService:
    def __init__(self, classifier: PlaceClassifier):
        self.classifier = classifier
        self.feedback_buffer = []
        self.buffer_size = 100
        self.retrain_threshold = 500
    
    async def collect_feedback(self, place_id: str, predicted_category: str, actual_category: str):
        """사용자 수정 피드백 수집"""
        feedback = {
            'place_id': place_id,
            'predicted': predicted_category,
            'actual': actual_category,
            'timestamp': datetime.utcnow()
        }
        
        self.feedback_buffer.append(feedback)
        
        # 버퍼가 가득 차면 재학습 큐에 추가
        if len(self.feedback_buffer) >= self.retrain_threshold:
            await self.trigger_retraining()
    
    async def trigger_retraining(self):
        # 백그라운드 작업으로 모델 재학습
        retrain_task.delay(self.feedback_buffer.copy())
        self.feedback_buffer.clear()

@celery_app.task
def retrain_model(feedback_data: List[dict]):
    """모델 재학습 백그라운드 작업"""
    # 기존 학습 데이터와 피드백 데이터 결합
    training_data = load_training_data()
    
    for feedback in feedback_data:
        place = get_place_by_id(feedback['place_id'])
        training_data.append((
            place.name,
            place.address,
            feedback['actual']
        ))
    
    # 새 모델 학습
    classifier = PlaceClassifier()
    classifier.train(training_data)
    
    # A/B 테스트를 위한 모델 배포
    deploy_model_for_testing(classifier)
```

---

## 6. 중복 감지 시스템

### 6-1. 중복 감지 알고리즘
```python
from difflib import SequenceMatcher
import re
from geopy.distance import geodesic

class DuplicateDetector:
    def __init__(self):
        self.similarity_threshold = 0.8
        self.distance_threshold_meters = 50
    
    def normalize_name(self, name: str) -> str:
        """장소명 정규화"""
        # 특수문자 제거
        normalized = re.sub(r'[^\w\s]', '', name)
        
        # 공통 접두사/접미사 제거 (카페, 레스토랑 등)
        prefixes = ['카페', '커피', '레스토랑', '식당', '갤러리', '뮤지엄']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        # 소문자 변환 및 공백 정리
        return re.sub(r'\s+', ' ', normalized.lower().strip())
    
    def normalize_address(self, address: str) -> str:
        """주소 정규화"""
        if not address:
            return ""
        
        # 상세 주소 제거 (층, 호수 등)
        address = re.sub(r'\d+층|\d+호|B\d+F?|\d+F', '', address)
        
        # 도로명 주소 우선 (지번 주소 제거)
        parts = address.split(',')
        if len(parts) > 1:
            # 가장 구체적인 주소 사용
            address = parts[0].strip()
        
        return address.strip()
    
    async def find_duplicates(self, user_id: str, name: str, address: str = None, coordinates: Coordinates = None) -> List[Place]:
        normalized_name = self.normalize_name(name)
        normalized_address = self.normalize_address(address or "")
        
        # 1차: 이름 유사도 검사
        name_candidates = await self._find_by_name_similarity(user_id, normalized_name)
        
        # 2차: 주소 또는 좌표 검사
        final_candidates = []
        
        for candidate in name_candidates:
            candidate_name = self.normalize_name(candidate.name)
            candidate_address = self.normalize_address(candidate.address or "")
            
            # 이름 유사도 계산
            name_similarity = SequenceMatcher(None, normalized_name, candidate_name).ratio()
            
            if name_similarity >= self.similarity_threshold:
                # 좌표가 있으면 거리 검사
                if coordinates and candidate.coordinates:
                    distance = geodesic(
                        (coordinates.lat, coordinates.lng),
                        (candidate.coordinates.lat, candidate.coordinates.lng)
                    ).meters
                    
                    if distance <= self.distance_threshold_meters:
                        final_candidates.append(candidate)
                
                # 주소 유사도 검사
                elif normalized_address and candidate_address:
                    address_similarity = SequenceMatcher(None, normalized_address, candidate_address).ratio()
                    
                    if address_similarity >= 0.6:  # 주소는 조금 더 관대하게
                        final_candidates.append(candidate)
        
        return final_candidates
    
    async def _find_by_name_similarity(self, user_id: str, normalized_name: str) -> List[Place]:
        # Elasticsearch의 fuzzy 검색 활용
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {
                            "multi_match": {
                                "query": normalized_name,
                                "fields": ["name^2", "name.ngram"],
                                "fuzziness": "AUTO",
                                "minimum_should_match": "70%"
                            }
                        }
                    ]
                }
            },
            "size": 10
        }
        
        response = await self.elasticsearch.search(
            index="places",
            body=search_body
        )
        
        place_ids = [hit["_source"]["place_id"] for hit in response["hits"]["hits"]]
        return await self.place_repository.find_by_ids(place_ids)
```

### 6-2. 중복 해결 UI 로직
```python
class DuplicateResolutionService:
    def __init__(self, duplicate_detector: DuplicateDetector):
        self.duplicate_detector = duplicate_detector
    
    async def handle_potential_duplicate(self, user_id: str, place_data: PlaceCreateRequest) -> PlaceResolutionResponse:
        duplicates = await self.duplicate_detector.find_duplicates(
            user_id, 
            place_data.name, 
            place_data.address,
            place_data.coordinates
        )
        
        if not duplicates:
            # 중복 없음 - 바로 생성
            new_place = await self.place_service.create_place(user_id, place_data)
            return PlaceResolutionResponse(
                action="created",
                place=new_place
            )
        
        # 중복 발견 - 사용자 선택 필요
        return PlaceResolutionResponse(
            action="duplicate_found",
            candidates=duplicates,
            suggested_actions=[
                {"action": "merge", "description": "기존 장소에 정보 병합"},
                {"action": "update", "description": "기존 장소 정보 업데이트"},  
                {"action": "create_anyway", "description": "새 장소로 추가"}
            ]
        )

@router.post("/places/resolve-duplicate")
async def resolve_duplicate(
    resolution: DuplicateResolutionRequest,
    current_user: User = Depends(get_current_user),
    resolver: DuplicateResolutionService = Depends()
):
    if resolution.action == "merge":
        result = await resolver.merge_places(
            current_user.id,
            resolution.existing_place_id,
            resolution.new_place_data
        )
    elif resolution.action == "update":
        result = await resolver.update_existing_place(
            current_user.id,
            resolution.existing_place_id,
            resolution.new_place_data
        )
    else:  # create_anyway
        result = await resolver.create_new_place(
            current_user.id,
            resolution.new_place_data
        )
    
    return result
```

---

## 7. 상태 관리 시스템

### 7-1. 상태 전이 관리
```python
from enum import Enum
from typing import Dict, Set

class PlaceStatus(str, Enum):
    WISHLIST = "wishlist"      # 가보고 싶음
    FAVORITE = "favorite"      # 즐겨찾기  
    PLANNED = "planned"        # 방문 예정
    VISITED = "visited"        # 방문 완료

class PlaceStatusManager:
    # 허용된 상태 전이 정의
    ALLOWED_TRANSITIONS: Dict[PlaceStatus, Set[PlaceStatus]] = {
        PlaceStatus.WISHLIST: {PlaceStatus.FAVORITE, PlaceStatus.PLANNED, PlaceStatus.VISITED},
        PlaceStatus.FAVORITE: {PlaceStatus.PLANNED, PlaceStatus.VISITED, PlaceStatus.WISHLIST},
        PlaceStatus.PLANNED: {PlaceStatus.VISITED, PlaceStatus.FAVORITE, PlaceStatus.WISHLIST},
        PlaceStatus.VISITED: {PlaceStatus.FAVORITE, PlaceStatus.PLANNED}  # 재방문 가능
    }
    
    def can_transition(self, from_status: PlaceStatus, to_status: PlaceStatus) -> bool:
        return to_status in self.ALLOWED_TRANSITIONS.get(from_status, set())
    
    async def update_status(self, user_id: str, place_id: str, new_status: PlaceStatus) -> Place:
        place = await self.place_repository.get_by_id(user_id, place_id)
        if not place:
            raise PlaceNotFoundError()
        
        current_status = PlaceStatus(place.status)
        
        if not self.can_transition(current_status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {current_status} to {new_status}"
            )
        
        # 상태별 추가 처리
        update_data = {"status": new_status}
        
        if new_status == PlaceStatus.VISITED:
            update_data.update({
                "visit_count": place.visit_count + 1,
                "last_visited_at": datetime.utcnow()
            })
        
        updated_place = await self.place_repository.update(place_id, update_data)
        
        # 상태 변경 이벤트 발행
        await self.event_publisher.publish(PlaceStatusChangedEvent(
            user_id=user_id,
            place_id=place_id,
            old_status=current_status,
            new_status=new_status,
            timestamp=datetime.utcnow()
        ))
        
        return updated_place
```

### 7-2. 배치 상태 업데이트
```python
class BatchStatusUpdater:
    async def bulk_update_status(self, user_id: str, place_ids: List[str], new_status: PlaceStatus) -> BulkUpdateResult:
        results = []
        errors = []
        
        for place_id in place_ids:
            try:
                updated_place = await self.status_manager.update_status(user_id, place_id, new_status)
                results.append(updated_place)
            except Exception as e:
                errors.append(BulkUpdateError(place_id=place_id, error=str(e)))
        
        return BulkUpdateResult(
            success_count=len(results),
            error_count=len(errors),
            updated_places=results,
            errors=errors
        )

# API 엔드포인트
@router.put("/places/bulk-status")
async def bulk_update_status(
    request: BulkStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    updater: BatchStatusUpdater = Depends()
):
    if len(request.place_ids) > 50:
        raise HTTPException(400, "최대 50개까지 일괄 업데이트 가능합니다")
    
    result = await updater.bulk_update_status(
        current_user.id,
        request.place_ids,
        request.new_status
    )
    
    return result
```

---

## 8. 캐싱 전략

### 8-1. 다계층 캐싱
```python
class PlaceCacheManager:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.local_cache = TTLCache(maxsize=1000, ttl=300)
    
    async def get_user_places(self, user_id: str, filters: PlaceFilters) -> Optional[List[Place]]:
        cache_key = self._generate_cache_key(user_id, filters)
        
        # L1: 로컬 캐시
        cached = self.local_cache.get(cache_key)
        if cached:
            return cached
        
        # L2: Redis 캐시
        redis_data = await self.redis.get(cache_key)
        if redis_data:
            places = [Place.parse_raw(data) for data in json.loads(redis_data)]
            self.local_cache[cache_key] = places
            return places
        
        return None
    
    async def set_user_places(self, user_id: str, filters: PlaceFilters, places: List[Place]):
        cache_key = self._generate_cache_key(user_id, filters)
        
        # L1: 로컬 캐시
        self.local_cache[cache_key] = places
        
        # L2: Redis 캐시 (더 긴 TTL)
        redis_data = json.dumps([place.json() for place in places])
        await self.redis.setex(cache_key, timedelta(minutes=30), redis_data)
    
    async def invalidate_user_cache(self, user_id: str):
        """사용자의 모든 캐시 무효화"""
        pattern = f"hotly:places:{user_id}:*"
        
        # Redis 캐시 무효화
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        
        # 로컬 캐시 무효화 (패턴 매칭 불가능하므로 전체 클리어)
        self.local_cache.clear()
    
    def _generate_cache_key(self, user_id: str, filters: PlaceFilters) -> str:
        filter_hash = hashlib.md5(filters.json().encode()).hexdigest()[:8]
        return f"hotly:places:{user_id}:{filter_hash}"

# 캐시 무효화 이벤트 처리
class CacheEventHandler:
    def __init__(self, cache_manager: PlaceCacheManager):
        self.cache_manager = cache_manager
    
    async def handle_place_updated(self, event: PlaceUpdatedEvent):
        await self.cache_manager.invalidate_user_cache(event.user_id)
    
    async def handle_place_deleted(self, event: PlaceDeletedEvent):
        await self.cache_manager.invalidate_user_cache(event.user_id)
```

### 8-2. 스마트 캐싱
```python
class SmartCacheManager(PlaceCacheManager):
    async def get_popular_tags(self, user_id: str) -> List[str]:
        cache_key = f"hotly:popular_tags:{user_id}"
        
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # DB에서 조회
        tags = await self.tag_service.get_popular_tags(user_id, limit=20)
        
        # 1시간 캐싱
        await self.redis.setex(cache_key, timedelta(hours=1), json.dumps(tags))
        
        return tags
    
    async def warm_up_cache(self, user_id: str):
        """사용자 캐시 사전 로딩"""
        common_filters = [
            PlaceFilters(),  # 기본 필터
            PlaceFilters(status=PlaceStatus.FAVORITE),  # 즐겨찾기
            PlaceFilters(category=PlaceCategory.CAFE),  # 카페만
            PlaceFilters(category=PlaceCategory.RESTAURANT),  # 맛집만
        ]
        
        # 백그라운드에서 캐시 워밍업
        for filters in common_filters:
            asyncio.create_task(self._warm_up_filter_cache(user_id, filters))
    
    async def _warm_up_filter_cache(self, user_id: str, filters: PlaceFilters):
        places = await self.place_service.get_places(user_id, filters)
        await self.set_user_places(user_id, filters, places)
```

---

## 9. 검색 및 필터링

### 9-1. Elasticsearch 검색 서비스
```python
class PlaceSearchService:
    def __init__(self):
        self.es_client = Elasticsearch([settings.ELASTICSEARCH_URL])
        self.index_name = "places"
    
    async def search_places(self, user_id: str, query: SearchQuery) -> SearchResult:
        search_body = self._build_search_query(user_id, query)
        
        response = await self.es_client.search(
            index=self.index_name,
            body=search_body
        )
        
        places = []
        for hit in response["hits"]["hits"]:
            place_id = hit["_source"]["place_id"]
            place = await self.place_repository.get_by_id(user_id, place_id)
            if place:
                # 검색 점수 추가
                place.search_score = hit["_score"]
                places.append(place)
        
        return SearchResult(
            places=places,
            total_count=response["hits"]["total"]["value"],
            max_score=response["hits"]["max_score"]
        )
    
    def _build_search_query(self, user_id: str, query: SearchQuery) -> dict:
        must_clauses = [{"term": {"user_id": user_id}}]
        should_clauses = []
        filter_clauses = []
        
        # 텍스트 검색
        if query.text:
            should_clauses.extend([
                {
                    "match": {
                        "name": {
                            "query": query.text,
                            "boost": 3.0,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                {
                    "match": {
                        "address": {
                            "query": query.text,
                            "boost": 1.5
                        }
                    }
                },
                {
                    "terms": {
                        "user_tags": query.text.split(),
                        "boost": 2.0
                    }
                }
            ])
        
        # 카테고리 필터
        if query.categories:
            filter_clauses.append({
                "terms": {"category": query.categories}
            })
        
        # 상태 필터
        if query.statuses:
            filter_clauses.append({
                "terms": {"status": query.statuses}
            })
        
        # 태그 필터
        if query.tags:
            filter_clauses.append({
                "terms": {"user_tags": query.tags}
            })
        
        # 지리적 검색
        if query.location and query.radius:
            filter_clauses.append({
                "geo_distance": {
                    "distance": f"{query.radius}km",
                    "location": {
                        "lat": query.location.lat,
                        "lon": query.location.lng
                    }
                }
            })
        
        # 평점 범위
        if query.min_rating:
            filter_clauses.append({
                "range": {"rating": {"gte": query.min_rating}}
            })
        
        search_query = {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "filter": filter_clauses,
                "minimum_should_match": 1 if should_clauses else 0
            }
        }
        
        # 정렬
        sort = self._build_sort_clause(query.sort)
        
        return {
            "query": search_query,
            "sort": sort,
            "size": query.limit,
            "from": query.offset,
            "highlight": {
                "fields": {
                    "name": {},
                    "address": {}
                }
            }
        }
    
    def _build_sort_clause(self, sort: PlaceSortBy) -> List[dict]:
        sort_mapping = {
            PlaceSortBy.RELEVANCE: [{"_score": "desc"}],
            PlaceSortBy.CREATED_DESC: [{"created_at": "desc"}],
            PlaceSortBy.CREATED_ASC: [{"created_at": "asc"}],
            PlaceSortBy.NAME_ASC: [{"name.keyword": "asc"}],
            PlaceSortBy.NAME_DESC: [{"name.keyword": "desc"}],
            PlaceSortBy.RATING_DESC: [{"rating": {"order": "desc", "missing": "_last"}}],
        }
        
        return sort_mapping.get(sort, [{"_score": "desc"}])
```

### 9-2. 자동완성 서비스
```python
class AutocompleteService:
    async def suggest_names(self, user_id: str, query: str, limit: int = 10) -> List[str]:
        """장소명 자동완성"""
        search_body = {
            "suggest": {
                "place_name_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "name_suggest",
                        "contexts": {
                            "user_id": user_id
                        },
                        "size": limit
                    }
                }
            }
        }
        
        response = await self.es_client.search(
            index=self.index_name,
            body=search_body
        )
        
        suggestions = []
        for option in response["suggest"]["place_name_suggest"][0]["options"]:
            suggestions.append(option["text"])
        
        return suggestions
    
    async def suggest_tags(self, user_id: str, query: str, limit: int = 10) -> List[TagSuggestion]:
        """태그 자동완성"""
        # Redis에서 사용자 태그 통계 조회
        pattern = f"hotly:user_tags:{user_id}:*{query}*"
        keys = await self.redis.keys(pattern)
        
        suggestions = []
        for key in keys[:limit]:
            tag = key.split(":")[-1]
            usage_count = await self.redis.get(key)
            suggestions.append(TagSuggestion(
                tag=tag,
                usage_count=int(usage_count or 0)
            ))
        
        # 사용 빈도순 정렬
        suggestions.sort(key=lambda x: x.usage_count, reverse=True)
        
        return suggestions
```

---

## 10. 테스트 전략

### 10-1. 단위 테스트 (TDD)
```python
import pytest
from unittest.mock import AsyncMock

class TestPlaceService:
    @pytest.fixture
    def place_service(self):
        return PlaceService(
            repository=AsyncMock(),
            classifier=AsyncMock(),
            duplicate_detector=AsyncMock(),
            cache_manager=AsyncMock()
        )
    
    async def test_create_place_with_auto_classification(self, place_service):
        # Given
        user_id = "user123"
        place_request = PlaceCreateRequest(
            name="스타벅스 강남점",
            address="서울시 강남구 테헤란로 123"
        )
        
        place_service.classifier.classify_place.return_value = ("cafe", 0.95)
        place_service.duplicate_detector.find_duplicates.return_value = []
        place_service.repository.create.return_value = Place(
            place_id="place123",
            user_id=user_id,
            name="스타벅스 강남점",
            category=PlaceCategory.CAFE,
            auto_category_confidence=0.95
        )
        
        # When
        result = await place_service.create_place(user_id, place_request)
        
        # Then
        assert result.category == PlaceCategory.CAFE
        assert result.auto_category_confidence == 0.95
        place_service.classifier.classify_place.assert_called_once_with(
            place_request.name, place_request.address
        )
    
    async def test_create_place_with_duplicate_detection(self, place_service):
        # Given
        user_id = "user123"
        place_request = PlaceCreateRequest(name="중복 카페")
        
        existing_place = Place(place_id="existing123", name="중복 카페")
        place_service.duplicate_detector.find_duplicates.return_value = [existing_place]
        
        # When & Then
        with pytest.raises(PlaceDuplicateError) as exc_info:
            await place_service.create_place(user_id, place_request)
        
        assert "이미 저장된 장소입니다" in str(exc_info.value)

class TestDuplicateDetector:
    def test_normalize_name(self):
        detector = DuplicateDetector()
        
        # Given & When & Then
        assert detector.normalize_name("카페 테스트") == "테스트"
        assert detector.normalize_name("스타벅스!!!") == "스타벅스"
        assert detector.normalize_name("  커피   빈  ") == "빈"
    
    async def test_find_duplicates_by_similarity(self):
        # Given
        detector = DuplicateDetector()
        detector._find_by_name_similarity = AsyncMock(return_value=[
            Place(name="스타벅스 강남점", address="강남구 테헤란로 123")
        ])
        
        # When
        duplicates = await detector.find_duplicates(
            "user123", 
            "스타벅스 강남", 
            "강남구 테헤란로 123"
        )
        
        # Then
        assert len(duplicates) == 1
        assert "스타벅스" in duplicates[0].name
```

### 10-2. 통합 테스트
```python
class TestPlaceManagementIntegration:
    @pytest.mark.integration
    async def test_place_crud_workflow(self, test_client, postgresql, redis_client):
        # 장소 생성
        create_response = await test_client.post(
            "/api/v1/places",
            json={
                "name": "테스트 카페",
                "address": "서울시 강남구",
                "user_tags": ["힙한", "조용한"]
            }
        )
        
        assert create_response.status_code == 201
        place_data = create_response.json()
        place_id = place_data["place_id"]
        
        # 장소 조회
        get_response = await test_client.get(f"/api/v1/places/{place_id}")
        assert get_response.status_code == 200
        
        # 상태 업데이트
        status_response = await test_client.put(
            f"/api/v1/places/{place_id}/status",
            json={"status": "favorite"}
        )
        assert status_response.status_code == 200
        
        # 태그 업데이트
        tag_response = await test_client.put(
            f"/api/v1/places/{place_id}/tags",
            json={"tags": ["힙한", "조용한", "와이파이좋음"]}
        )
        assert tag_response.status_code == 200
        
        # 장소 삭제
        delete_response = await test_client.delete(f"/api/v1/places/{place_id}")
        assert delete_response.status_code == 204
    
    @pytest.mark.integration
    async def test_search_and_filter(self, test_client, elasticsearch):
        # 테스트 데이터 생성
        places = [
            {"name": "스타벅스", "category": "cafe", "user_tags": ["체인", "wifi"]},
            {"name": "로컬 카페", "category": "cafe", "user_tags": ["로컬", "조용한"]},
            {"name": "맥도날드", "category": "restaurant", "user_tags": ["패스트푸드"]}
        ]
        
        for place in places:
            await test_client.post("/api/v1/places", json=place)
        
        # 검색 테스트
        search_response = await test_client.get(
            "/api/v1/places/search?q=카페&category=cafe"
        )
        
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results["places"]) == 2
```

---

## 11. 모니터링 및 운영

### 11-1. 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
place_operations_total = Counter(
    'place_operations_total',
    'Total number of place operations',
    ['operation', 'status']
)

duplicate_detection_duration = Histogram(
    'duplicate_detection_duration_seconds',
    'Time spent on duplicate detection',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

active_places_total = Gauge(
    'active_places_total',
    'Total number of active places',
    ['category', 'status']
)

class PlaceMetricsCollector:
    def record_place_operation(self, operation: str, status: str):
        place_operations_total.labels(operation=operation, status=status).inc()
    
    def record_duplicate_detection(self, duration: float):
        duplicate_detection_duration.observe(duration)
    
    def update_place_counts(self):
        # 주기적으로 실행되는 통계 업데이트
        asyncio.create_task(self._update_place_statistics())
    
    async def _update_place_statistics(self):
        stats = await self.place_repository.get_statistics()
        
        for category in PlaceCategory:
            for status in PlaceStatus:
                count = stats.get(f"{category}_{status}", 0)
                active_places_total.labels(category=category, status=status).set(count)
```

### 11-2. 성능 모니터링
```python
class PerformanceMonitor:
    def __init__(self):
        self.slow_query_threshold = 1.0  # 1초
    
    async def monitor_database_performance(self):
        """DB 쿼리 성능 모니터링"""
        # PostgreSQL 쿼리 로깅 활성화
        await self.postgresql.execute("""
            ALTER SYSTEM SET log_min_duration_statement = 100;
            SELECT pg_reload_conf();
        """)
    
    async def check_slow_queries(self):
        """느린 쿼리 감지 및 알림"""
        slow_queries = await self.postgresql.fetch("""
            SELECT query, total_time, calls, mean_time
            FROM pg_stat_statements 
            WHERE mean_time > $1
            ORDER BY mean_time DESC
            LIMIT 10
        """, self.slow_query_threshold * 1000)
        
        for query in slow_queries:
            logger.warning(
                "Slow query detected",
                query=query["query"][:100],  # 쿼리 앞부분만
                duration_ms=query["mean_time"],
                calls=query["calls"]
            )
    
    async def monitor_cache_hit_rates(self):
        """캐시 적중률 모니터링"""
        info = await self.redis.info("stats")
        
        cache_hits = info.get("keyspace_hits", 0)
        cache_misses = info.get("keyspace_misses", 0)
        
        if cache_hits + cache_misses > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            
            if hit_rate < 0.7:  # 70% 미만이면 경고
                logger.warning(
                    "Low cache hit rate",
                    hit_rate=hit_rate,
                    hits=cache_hits,
                    misses=cache_misses
                )
```

---

## 12. 용어 사전(Technical)
- **JSONB:** PostgreSQL의 효율적인 JSON 바이너리 저장 형식
- **Full-text Search:** 문서 내 모든 텍스트를 대상으로 하는 검색
- **Fuzzy Matching:** 완전 일치하지 않아도 유사한 문자열을 찾는 기법
- **N-gram:** 연속된 N개의 문자 또는 단어로 구성된 시퀀스
- **Geospatial Index:** 지리적 좌표를 효율적으로 검색하기 위한 인덱스

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 02-place-management 버전과 연동