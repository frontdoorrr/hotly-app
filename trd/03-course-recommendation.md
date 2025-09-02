# TRD: AI 기반 데이트 코스 추천

## 1. 기술 개요
**목적:** PRD 03-course-recommendation 요구사항을 충족하기 위한 AI 기반 코스 최적화 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- 최적화 알고리즘: Simulated Annealing + Genetic Algorithm
- 경로 계산: Kakao Map API + Google Directions API
- AI/ML: 사용자 선호도 학습 모델 (Collaborative Filtering)
- 캐시: Redis (경로 정보, 영업시간)
- API: FastAPI + Pydantic

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Mobile App]
    ↓ POST /api/v1/courses/generate
[API Gateway + Rate Limiter]
    ↓
[FastAPI Service]
    ↓
[Course Generator Engine] → [Optimization Service]
    ↓                            ↓
[Route Calculator] ←→ [External APIs] (Kakao/Google Maps)
    ↓
[Preference Engine] → [User Profile Service]
    ↓
[Validation & Scoring]
    ↓
[PostgreSQL] + [Redis Cache]
```

### 2-2. 마이크로서비스 분해
```
1. Course Generation Service
   - 코스 생성 로직 총괄
   - 사용자 입력 검증
   - 결과 집계 및 응답

2. Optimization Engine Service
   - 유전 알고리즘/시뮬레이티드 어닐링
   - 제약 조건 관리
   - 점수 계산

3. Route Calculation Service
   - 외부 지도 API 연동
   - 이동시간/거리 계산
   - 대중교통 경로 분석

4. Preference Service
   - 사용자 선호도 분석
   - 패턴 학습 및 추천
   - 개인화 가중치 계산
```

---

## 3. API 설계

### 3-1. 코스 생성 요청
```python
# Request Schema
class CourseGenerateRequest(BaseModel):
    place_ids: List[str] = Field(..., min_items=3, max_items=6)
    transport_method: TransportMethod = TransportMethod.WALKING
    start_time: time = Field(default=time(10, 0))
    preferences: Optional[CoursePreferences] = None
    user_id: Optional[str] = None

class CoursePreferences(BaseModel):
    category_order: Optional[List[str]] = None
    max_total_duration: int = Field(default=600, ge=240, le=720)  # minutes
    avoid_rush_hours: bool = True
    preferred_stay_duration: Dict[str, int] = {}

class TransportMethod(str, Enum):
    WALKING = "walking"
    TRANSIT = "transit"
    DRIVING = "driving"
    MIXED = "mixed"

# Response Schema
class CourseGenerateResponse(BaseModel):
    course_id: str
    course: CourseDetail
    optimization_score: float
    generation_time_ms: int
    alternatives: Optional[List[CourseAlternative]] = None

class CourseDetail(BaseModel):
    name: str
    places: List[CoursePlaceDetail]
    total_duration: int  # minutes
    total_distance: int  # meters
    estimated_cost: Optional[CostBreakdown] = None
    difficulty_level: DifficultyLevel

class CoursePlaceDetail(BaseModel):
    place_id: str
    place_name: str
    order: int
    arrival_time: time
    departure_time: time
    stay_duration: int
    travel_to_next: Optional[TravelSegment] = None
    visit_rating: float  # 이 시간대 방문 추천도
```

### 3-2. 코스 편집 API
```python
class CourseEditRequest(BaseModel):
    course_id: str
    modifications: List[CourseModification]

class CourseModification(BaseModel):
    type: ModificationType
    place_id: Optional[str] = None
    new_order: Optional[int] = None
    new_stay_duration: Optional[int] = None
    replacement_place_id: Optional[str] = None

class ModificationType(str, Enum):
    REORDER = "reorder"
    CHANGE_DURATION = "change_duration"
    REPLACE_PLACE = "replace_place"
    REMOVE_PLACE = "remove_place"
    ADD_PLACE = "add_place"

class CourseEditResponse(BaseModel):
    updated_course: CourseDetail
    impact_analysis: ModificationImpact
    
class ModificationImpact(BaseModel):
    time_change: int  # minutes difference
    distance_change: int  # meters difference
    score_change: float
    affected_places: List[str]
```

---

## 4. 최적화 엔진 설계

### 4-1. 유전 알고리즘 구현
```python
class GeneticOptimizer:
    def __init__(self, config: OptimizationConfig):
        self.population_size = config.population_size  # 50
        self.generations = config.generations  # 100
        self.mutation_rate = config.mutation_rate  # 0.1
        self.crossover_rate = config.crossover_rate  # 0.8
    
    def optimize(self, places: List[Place], constraints: Constraints) -> CourseArrangement:
        # 초기 개체군 생성
        population = self._initialize_population(places)
        
        for generation in range(self.generations):
            # 적합도 평가
            fitness_scores = [self._evaluate_fitness(individual, constraints) 
                            for individual in population]
            
            # 선택
            selected = self._tournament_selection(population, fitness_scores)
            
            # 교배
            offspring = self._crossover(selected)
            
            # 돌연변이
            offspring = self._mutate(offspring)
            
            # 차세대 생성
            population = self._select_next_generation(population + offspring, fitness_scores)
            
            # 조기 종료 조건
            if self._convergence_check(fitness_scores):
                break
        
        return self._get_best_individual(population, fitness_scores)
    
    def _evaluate_fitness(self, arrangement: List[int], constraints: Constraints) -> float:
        """
        종합 적합도 점수 계산
        - 이동거리 최적화: 40%
        - 영업시간 적합성: 25%
        - 카테고리 다양성: 20%
        - 혼잡도 회피: 10%
        - 개인 선호도: 5%
        """
        distance_score = self._calculate_distance_score(arrangement)
        time_score = self._calculate_time_feasibility(arrangement)
        diversity_score = self._calculate_category_diversity(arrangement)
        crowd_score = self._calculate_crowd_avoidance(arrangement)
        preference_score = self._calculate_user_preference(arrangement)
        
        total_score = (
            distance_score * 0.4 +
            time_score * 0.25 +
            diversity_score * 0.2 +
            crowd_score * 0.1 +
            preference_score * 0.05
        )
        
        return total_score
```

### 4-2. 시뮬레이티드 어닐링 구현
```python
class SimulatedAnnealingOptimizer:
    def __init__(self, config: SAConfig):
        self.initial_temp = config.initial_temp  # 1000
        self.cooling_rate = config.cooling_rate  # 0.95
        self.min_temp = config.min_temp  # 1
        self.max_iterations = config.max_iterations  # 1000
    
    def optimize(self, initial_solution: List[int], constraints: Constraints) -> CourseArrangement:
        current_solution = initial_solution.copy()
        current_cost = self._calculate_cost(current_solution, constraints)
        best_solution = current_solution.copy()
        best_cost = current_cost
        
        temperature = self.initial_temp
        
        for iteration in range(self.max_iterations):
            if temperature < self.min_temp:
                break
            
            # 이웃 해 생성 (2-opt, 3-opt, insertion)
            neighbor = self._generate_neighbor(current_solution)
            neighbor_cost = self._calculate_cost(neighbor, constraints)
            
            # 해 수락 여부 결정
            if self._accept_solution(current_cost, neighbor_cost, temperature):
                current_solution = neighbor
                current_cost = neighbor_cost
                
                if neighbor_cost < best_cost:
                    best_solution = neighbor.copy()
                    best_cost = neighbor_cost
            
            temperature *= self.cooling_rate
        
        return CourseArrangement(
            order=best_solution,
            cost=best_cost,
            optimization_method="simulated_annealing"
        )
    
    def _generate_neighbor(self, solution: List[int]) -> List[int]:
        """이웃 해 생성 전략"""
        neighbor_type = random.choice(['swap', 'insert', 'reverse'])
        
        if neighbor_type == 'swap':
            return self._swap_two_cities(solution)
        elif neighbor_type == 'insert':
            return self._insert_city(solution)
        else:
            return self._reverse_segment(solution)
```

---

## 5. 경로 계산 시스템

### 5-1. 외부 API 통합
```python
class RouteCalculator:
    def __init__(self):
        self.kakao_client = KakaoMapClient(api_key=settings.KAKAO_API_KEY)
        self.google_client = GoogleMapsClient(api_key=settings.GOOGLE_API_KEY)
        self.cache = RouteCache()
    
    async def calculate_route_matrix(
        self, 
        places: List[Place], 
        transport_method: TransportMethod
    ) -> RouteMatrix:
        """모든 장소 간 이동시간/거리 매트릭스 계산"""
        cache_key = self._generate_cache_key(places, transport_method)
        cached_result = await self.cache.get(cache_key)
        
        if cached_result:
            return RouteMatrix.parse_obj(cached_result)
        
        if transport_method == TransportMethod.WALKING:
            matrix = await self._calculate_walking_matrix(places)
        elif transport_method == TransportMethod.DRIVING:
            matrix = await self._calculate_driving_matrix(places)
        elif transport_method == TransportMethod.TRANSIT:
            matrix = await self._calculate_transit_matrix(places)
        else:  # MIXED
            matrix = await self._calculate_mixed_matrix(places)
        
        await self.cache.set(cache_key, matrix.dict(), ttl=3600)  # 1시간 캐시
        return matrix
    
    async def _calculate_walking_matrix(self, places: List[Place]) -> RouteMatrix:
        """도보 경로 매트릭스 계산"""
        n = len(places)
        distances = [[0] * n for _ in range(n)]
        durations = [[0] * n for _ in range(n)]
        
        # 배치 요청으로 효율성 향상
        origins = [f"{place.latitude},{place.longitude}" for place in places]
        destinations = origins.copy()
        
        response = await self.kakao_client.distance_matrix(
            origins=origins,
            destinations=destinations,
            mode="walking"
        )
        
        for i, row in enumerate(response['rows']):
            for j, element in enumerate(row['elements']):
                if element['status'] == 'OK':
                    distances[i][j] = element['distance']['value']
                    durations[i][j] = element['duration']['value']
                else:
                    # Fallback to straight-line distance
                    distances[i][j] = self._calculate_haversine_distance(places[i], places[j])
                    durations[i][j] = distances[i][j] / 1.2  # 1.2m/s walking speed
        
        return RouteMatrix(
            distances=distances,
            durations=durations,
            transport_method=TransportMethod.WALKING
        )
```

### 5-2. 실시간 교통 정보 통합
```python
class TrafficAnalyzer:
    def __init__(self):
        self.traffic_cache = TrafficCache()
    
    async def get_congestion_factor(
        self, 
        origin: Place, 
        destination: Place, 
        departure_time: datetime
    ) -> float:
        """혼잡도 계수 계산 (1.0 = 정상, 2.0 = 2배 느림)"""
        
        # 시간대별 기본 혼잡도
        hour = departure_time.hour
        base_congestion = self._get_base_congestion_by_hour(hour)
        
        # 실시간 교통 정보
        real_time_factor = await self._get_real_time_traffic(origin, destination)
        
        # 요일별 가중치
        weekday_factor = self._get_weekday_factor(departure_time.weekday())
        
        # 특별 이벤트 확인 (축제, 행사 등)
        event_factor = await self._check_special_events(origin, destination, departure_time)
        
        total_factor = base_congestion * real_time_factor * weekday_factor * event_factor
        return min(total_factor, 3.0)  # 최대 3배까지만
    
    def _get_base_congestion_by_hour(self, hour: int) -> float:
        """시간대별 기본 혼잡도"""
        congestion_map = {
            range(6, 9): 1.8,    # 출근시간
            range(9, 11): 1.2,   # 오전
            range(11, 14): 1.4,  # 점심시간
            range(14, 17): 1.1,  # 오후
            range(17, 20): 1.9,  # 퇴근시간
            range(20, 22): 1.3,  # 저녁
            range(22, 24): 1.0,  # 심야
            range(0, 6): 1.0     # 새벽
        }
        
        for time_range, factor in congestion_map.items():
            if hour in time_range:
                return factor
        return 1.0
```

---

## 6. 사용자 선호도 엔진

### 6-1. 협업 필터링 구현
```python
class PreferenceEngine:
    def __init__(self):
        self.user_similarity_cache = {}
        self.place_embeddings = PlaceEmbeddings()
    
    def calculate_user_preferences(self, user_id: str) -> UserPreferences:
        """사용자 선호도 벡터 계산"""
        
        # 사용자 과거 행동 분석
        user_history = self._get_user_history(user_id)
        
        # 카테고리별 선호도
        category_prefs = self._analyze_category_preferences(user_history)
        
        # 시간대별 선호도
        time_prefs = self._analyze_time_preferences(user_history)
        
        # 동반자 유형별 선호도
        companion_prefs = self._analyze_companion_preferences(user_history)
        
        # 유사 사용자 기반 추천
        similar_users = self._find_similar_users(user_id)
        collaborative_prefs = self._collaborative_filtering(user_id, similar_users)
        
        return UserPreferences(
            category_weights=category_prefs,
            time_preferences=time_prefs,
            companion_preferences=companion_prefs,
            collaborative_scores=collaborative_prefs,
            confidence=self._calculate_confidence(user_history)
        )
    
    def _find_similar_users(self, user_id: str) -> List[Tuple[str, float]]:
        """유사 사용자 찾기 (코사인 유사도)"""
        target_vector = self._get_user_preference_vector(user_id)
        similarities = []
        
        # 활성 사용자들과 유사도 계산
        active_users = self._get_active_users(limit=1000)
        
        for other_user_id in active_users:
            if other_user_id == user_id:
                continue
            
            other_vector = self._get_user_preference_vector(other_user_id)
            similarity = self._cosine_similarity(target_vector, other_vector)
            
            if similarity > 0.3:  # 임계값 이상만
                similarities.append((other_user_id, similarity))
        
        # 상위 20명 반환
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:20]
    
    def _get_user_preference_vector(self, user_id: str) -> np.ndarray:
        """사용자 선호도 벡터 생성"""
        # 카테고리별 방문 빈도
        category_visits = self._get_category_visit_counts(user_id)
        
        # 평점 패턴
        rating_patterns = self._get_rating_patterns(user_id)
        
        # 시간대별 활동
        time_activity = self._get_time_activity_pattern(user_id)
        
        # 지역별 선호도
        location_prefs = self._get_location_preferences(user_id)
        
        # 벡터 결합
        vector = np.concatenate([
            category_visits,
            rating_patterns,
            time_activity,
            location_prefs
        ])
        
        # 정규화
        return vector / np.linalg.norm(vector)
```

### 6-2. 딥러닝 기반 추천
```python
class DeepRecommendationModel:
    def __init__(self):
        self.model = self._load_model()
        self.feature_encoder = FeatureEncoder()
    
    def predict_course_rating(
        self, 
        user_features: UserFeatures, 
        course_features: CourseFeatures
    ) -> float:
        """코스 만족도 예측"""
        
        # 피처 인코딩
        user_encoded = self.feature_encoder.encode_user(user_features)
        course_encoded = self.feature_encoder.encode_course(course_features)
        
        # 모델 입력 준비
        model_input = {
            'user_features': user_encoded,
            'course_features': course_encoded,
            'interaction_features': self._create_interaction_features(
                user_encoded, course_encoded
            )
        }
        
        # 예측 수행
        prediction = self.model.predict(model_input)
        return float(prediction[0])
    
    def _create_interaction_features(
        self, 
        user_features: np.ndarray, 
        course_features: np.ndarray
    ) -> np.ndarray:
        """사용자-코스 상호작용 피처 생성"""
        
        # 요소별 곱셈
        element_wise_product = user_features * course_features
        
        # 차이 계산
        difference = np.abs(user_features - course_features)
        
        # 내적
        dot_product = np.array([np.dot(user_features, course_features)])
        
        return np.concatenate([element_wise_product, difference, dot_product])
    
    def train_model(self, training_data: TrainingData):
        """모델 학습"""
        
        # 데이터 전처리
        X_user, X_course, X_interaction, y = self._prepare_training_data(training_data)
        
        # 모델 구조 정의
        user_input = layers.Input(shape=(X_user.shape[1],), name='user_features')
        course_input = layers.Input(shape=(X_course.shape[1],), name='course_features')
        interaction_input = layers.Input(shape=(X_interaction.shape[1],), name='interaction_features')
        
        # 사용자 임베딩 레이어
        user_dense = layers.Dense(128, activation='relu')(user_input)
        user_dense = layers.BatchNormalization()(user_dense)
        user_dense = layers.Dropout(0.3)(user_dense)
        
        # 코스 임베딩 레이어
        course_dense = layers.Dense(128, activation='relu')(course_input)
        course_dense = layers.BatchNormalization()(course_dense)
        course_dense = layers.Dropout(0.3)(course_dense)
        
        # 결합 레이어
        combined = layers.concatenate([user_dense, course_dense, interaction_input])
        combined = layers.Dense(256, activation='relu')(combined)
        combined = layers.BatchNormalization()(combined)
        combined = layers.Dropout(0.4)(combined)
        
        combined = layers.Dense(128, activation='relu')(combined)
        combined = layers.Dropout(0.3)(combined)
        
        output = layers.Dense(1, activation='sigmoid')(combined)
        
        model = Model(inputs=[user_input, course_input, interaction_input], outputs=output)
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # 학습
        model.fit(
            [X_user, X_course, X_interaction], 
            y,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[
                EarlyStopping(patience=10, restore_best_weights=True),
                ReduceLROnPlateau(patience=5)
            ]
        )
        
        self.model = model
```

---

## 7. 캐싱 전략

### 7-1. 다층 캐시 구조
```python
class CourseCache:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.local_cache = TTLCache(maxsize=500, ttl=300)  # 5분 로컬 캐시
    
    async def get_route_matrix(self, cache_key: str) -> Optional[RouteMatrix]:
        # L1: 로컬 메모리 캐시
        result = self.local_cache.get(cache_key)
        if result:
            return RouteMatrix.parse_obj(result)
        
        # L2: Redis 캐시
        cached_data = await self.redis.get(f"route_matrix:{cache_key}")
        if cached_data:
            result = json.loads(cached_data)
            self.local_cache[cache_key] = result
            return RouteMatrix.parse_obj(result)
        
        return None
    
    async def set_route_matrix(self, cache_key: str, matrix: RouteMatrix, ttl: int = 3600):
        data = matrix.dict()
        
        # L1 + L2 동시 저장
        self.local_cache[cache_key] = data
        await self.redis.setex(
            f"route_matrix:{cache_key}",
            ttl,
            json.dumps(data, default=str)
        )
    
    def _generate_route_cache_key(
        self, 
        places: List[Place], 
        transport_method: TransportMethod
    ) -> str:
        """경로 캐시 키 생성"""
        place_coords = [(p.latitude, p.longitude) for p in places]
        coord_hash = hashlib.md5(str(sorted(place_coords)).encode()).hexdigest()
        return f"{transport_method}_{coord_hash}"

class BusinessHoursCache:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
    
    async def get_business_hours(self, place_id: str, date: datetime.date) -> Optional[BusinessHours]:
        cache_key = f"business_hours:{place_id}:{date.isoformat()}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return BusinessHours.parse_raw(cached)
        return None
    
    async def set_business_hours(
        self, 
        place_id: str, 
        date: datetime.date, 
        hours: BusinessHours,
        ttl: int = 86400  # 24시간
    ):
        cache_key = f"business_hours:{place_id}:{date.isoformat()}"
        await self.redis.setex(cache_key, ttl, hours.json())
    
    async def invalidate_place_hours(self, place_id: str):
        """장소의 모든 영업시간 캐시 무효화"""
        pattern = f"business_hours:{place_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

---

## 8. 실시간 검증 및 조정

### 8-1. 영업시간 검증 시스템
```python
class BusinessHoursValidator:
    def __init__(self):
        self.external_sources = {
            'naver': NaverPlaceAPI(),
            'kakao': KakaoPlaceAPI(),
            'google': GooglePlacesAPI()
        }
        self.cache = BusinessHoursCache()
    
    async def validate_course_timing(self, course: CourseDetail) -> ValidationResult:
        """코스 전체 시간 검증"""
        issues = []
        suggestions = []
        
        for place_detail in course.places:
            place_id = place_detail.place_id
            arrival_time = place_detail.arrival_time
            departure_time = place_detail.departure_time
            
            # 영업시간 확인
            business_hours = await self._get_business_hours(place_id, arrival_time.date())
            
            if business_hours:
                if not self._is_time_within_hours(arrival_time, business_hours):
                    issues.append(
                        ValidationIssue(
                            type="CLOSED_DURING_VISIT",
                            place_id=place_id,
                            scheduled_time=arrival_time,
                            business_hours=business_hours
                        )
                    )
                    
                    # 대안 시간 제안
                    alternative_times = self._suggest_alternative_times(
                        business_hours, place_detail.stay_duration
                    )
                    suggestions.extend(alternative_times)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions
        )
    
    async def _get_business_hours(self, place_id: str, date: datetime.date) -> Optional[BusinessHours]:
        # 캐시에서 먼저 확인
        cached_hours = await self.cache.get_business_hours(place_id, date)
        if cached_hours:
            return cached_hours
        
        # 외부 소스에서 수집
        for source_name, source_api in self.external_sources.items():
            try:
                hours = await source_api.get_business_hours(place_id, date)
                if hours:
                    await self.cache.set_business_hours(place_id, date, hours)
                    return hours
            except Exception as e:
                logger.warning(f"Failed to get hours from {source_name}: {e}")
        
        return None
    
    def _suggest_alternative_times(
        self, 
        business_hours: BusinessHours, 
        stay_duration: int
    ) -> List[TimeSuggestion]:
        """영업시간에 맞는 대안 시간 제안"""
        suggestions = []
        
        for period in business_hours.open_periods:
            # 영업 시작 시간부터 체류시간을 고려하여 가능한 시간 계산
            latest_arrival = datetime.combine(
                datetime.today(),
                period.close_time
            ) - timedelta(minutes=stay_duration + 30)  # 30분 여유
            
            if period.open_time <= latest_arrival.time():
                suggestions.append(
                    TimeSuggestion(
                        suggested_arrival=period.open_time,
                        suggested_departure=datetime.combine(
                            datetime.today(), 
                            period.open_time
                        ) + timedelta(minutes=stay_duration),
                        reason="BUSINESS_HOURS_OPTIMAL"
                    )
                )
        
        return suggestions
```

### 8-2. 동적 코스 조정
```python
class DynamicCourseAdjuster:
    def __init__(self):
        self.traffic_analyzer = TrafficAnalyzer()
        self.weather_service = WeatherService()
    
    async def adjust_course_realtime(
        self, 
        course: CourseDetail, 
        current_location: Optional[Location] = None
    ) -> CourseAdjustment:
        """실시간 상황을 반영한 코스 조정"""
        
        adjustments = []
        
        # 현재 교통 상황 확인
        traffic_adjustment = await self._check_traffic_conditions(course)
        if traffic_adjustment:
            adjustments.append(traffic_adjustment)
        
        # 날씨 상황 확인
        weather_adjustment = await self._check_weather_impact(course)
        if weather_adjustment:
            adjustments.append(weather_adjustment)
        
        # 실시간 장소 상태 확인 (임시휴업, 혼잡도 등)
        place_status_adjustments = await self._check_place_status(course)
        adjustments.extend(place_status_adjustments)
        
        # 조정사항 적용
        adjusted_course = await self._apply_adjustments(course, adjustments)
        
        return CourseAdjustment(
            original_course=course,
            adjusted_course=adjusted_course,
            adjustments=adjustments,
            confidence=self._calculate_adjustment_confidence(adjustments)
        )
    
    async def _check_traffic_conditions(self, course: CourseDetail) -> Optional[TrafficAdjustment]:
        """교통 상황 기반 조정"""
        significant_delays = []
        
        for i in range(len(course.places) - 1):
            current_place = course.places[i]
            next_place = course.places[i + 1]
            
            # 예상 출발 시간의 교통 상황 확인
            departure_time = datetime.combine(datetime.today(), current_place.departure_time)
            
            congestion_factor = await self.traffic_analyzer.get_congestion_factor(
                origin=Place(id=current_place.place_id),
                destination=Place(id=next_place.place_id),
                departure_time=departure_time
            )
            
            # 원래 예상 시간과 현재 예상 시간 비교
            original_duration = current_place.travel_to_next.duration
            adjusted_duration = int(original_duration * congestion_factor)
            delay = adjusted_duration - original_duration
            
            if delay > 15:  # 15분 이상 지연 시
                significant_delays.append(
                    RouteDelay(
                        from_place=current_place.place_id,
                        to_place=next_place.place_id,
                        original_duration=original_duration,
                        adjusted_duration=adjusted_duration,
                        delay_reason="TRAFFIC_CONGESTION"
                    )
                )
        
        if significant_delays:
            return TrafficAdjustment(
                delays=significant_delays,
                suggested_action="RESCHEDULE_DEPARTURE_TIMES",
                impact_severity="MODERATE" if len(significant_delays) < 3 else "HIGH"
            )
        
        return None
```

---

## 9. 성능 최적화

### 9-1. 배치 처리 시스템
```python
class BatchOptimizer:
    def __init__(self):
        self.batch_size = 50
        self.processing_queue = asyncio.Queue(maxsize=1000)
        self.result_cache = {}
    
    async def process_batch_requests(self):
        """배치 요청 처리"""
        while True:
            batch = []
            try:
                # 배치 수집
                for _ in range(self.batch_size):
                    request = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=1.0
                    )
                    batch.append(request)
            except asyncio.TimeoutError:
                pass  # 시간 초과 시 현재 배치로 처리
            
            if batch:
                await self._process_optimization_batch(batch)
    
    async def _process_optimization_batch(self, batch: List[OptimizationRequest]):
        """최적화 요청 배치 처리"""
        
        # 유사한 요청 그룹화
        groups = self._group_similar_requests(batch)
        
        for group in groups:
            try:
                # 대표 케이스 최적화
                representative = group[0]
                optimized_result = await self._optimize_single_request(representative)
                
                # 결과를 그룹 내 유사 요청들에 적용
                for request in group:
                    adapted_result = self._adapt_result_to_request(
                        optimized_result, 
                        request
                    )
                    await self._send_result_to_client(request.request_id, adapted_result)
                    
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                # 실패한 요청들을 개별 처리 큐로 이동
                for request in group:
                    await self._queue_individual_processing(request)
    
    def _group_similar_requests(self, batch: List[OptimizationRequest]) -> List[List[OptimizationRequest]]:
        """유사한 최적화 요청 그룹화"""
        groups = []
        processed = set()
        
        for i, request1 in enumerate(batch):
            if i in processed:
                continue
            
            group = [request1]
            processed.add(i)
            
            for j, request2 in enumerate(batch[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_request_similarity(request1, request2)
                if similarity > 0.8:  # 80% 이상 유사
                    group.append(request2)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
```

### 9-2. 병렬 처리 최적화
```python
class ParallelProcessor:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_course_generation(self, request: CourseGenerateRequest) -> CourseGenerateResponse:
        """병렬 처리를 활용한 코스 생성"""
        
        start_time = time.time()
        
        # 병렬로 실행할 작업들 정의
        tasks = [
            self._fetch_place_details(request.place_ids),
            self._calculate_route_matrix(request.place_ids, request.transport_method),
            self._get_user_preferences(request.user_id),
            self._fetch_business_hours_batch(request.place_ids),
            self._get_weather_forecast()
        ]
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        place_details, route_matrix, user_prefs, business_hours, weather = results
        
        # 예외 처리
        if any(isinstance(result, Exception) for result in results):
            # 실패한 작업들에 대한 fallback 처리
            place_details = place_details if not isinstance(place_details, Exception) else await self._get_fallback_place_details(request.place_ids)
            route_matrix = route_matrix if not isinstance(route_matrix, Exception) else await self._get_fallback_route_matrix(request.place_ids)
            # ... 다른 fallback 처리
        
        # 최적화 수행
        async with self.semaphore:
            optimization_result = await self._run_optimization_parallel(
                place_details,
                route_matrix,
                user_prefs,
                business_hours,
                weather
            )
        
        generation_time = int((time.time() - start_time) * 1000)
        
        return CourseGenerateResponse(
            course_id=str(uuid.uuid4()),
            course=optimization_result.best_course,
            optimization_score=optimization_result.score,
            generation_time_ms=generation_time,
            alternatives=optimization_result.alternatives[:3]  # 상위 3개 대안
        )
    
    async def _run_optimization_parallel(
        self,
        place_details: List[Place],
        route_matrix: RouteMatrix,
        user_preferences: UserPreferences,
        business_hours: Dict[str, BusinessHours],
        weather: WeatherInfo
    ) -> OptimizationResult:
        """병렬 최적화 실행"""
        
        # 여러 최적화 알고리즘을 병렬로 실행
        optimization_tasks = [
            self._run_genetic_algorithm(place_details, route_matrix, user_preferences),
            self._run_simulated_annealing(place_details, route_matrix, user_preferences),
            self._run_greedy_heuristic(place_details, route_matrix, user_preferences)
        ]
        
        optimization_results = await asyncio.gather(*optimization_tasks)
        
        # 최고 결과 선택
        best_result = max(optimization_results, key=lambda x: x.score)
        
        # 추가 검증 및 조정
        validated_result = await self._validate_and_adjust(
            best_result, 
            business_hours, 
            weather
        )
        
        return OptimizationResult(
            best_course=validated_result.course,
            score=validated_result.score,
            alternatives=[r.course for r in optimization_results if r != best_result],
            optimization_method=best_result.method
        )
```

---

## 10. 모니터링 및 로깅

### 10-1. 성능 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge

class CourseMetrics:
    def __init__(self):
        self.generation_requests = Counter(
            'course_generation_requests_total',
            'Total course generation requests',
            ['transport_method', 'place_count', 'status']
        )
        
        self.generation_duration = Histogram(
            'course_generation_duration_seconds',
            'Time spent generating courses',
            ['transport_method', 'optimization_method'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
        )
        
        self.optimization_score = Histogram(
            'course_optimization_score',
            'Course optimization scores',
            ['optimization_method'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.active_optimizations = Gauge(
            'active_optimizations_count',
            'Current number of active optimizations'
        )
        
        self.cache_hits = Counter(
            'course_cache_hits_total',
            'Cache hit count',
            ['cache_type']
        )

class CourseLogger:
    def __init__(self):
        self.logger = structlog.get_logger()
        self.metrics = CourseMetrics()
    
    async def log_generation_request(
        self,
        request: CourseGenerateRequest,
        user_id: str,
        request_id: str
    ):
        self.metrics.generation_requests.labels(
            transport_method=request.transport_method,
            place_count=len(request.place_ids),
            status='started'
        ).inc()
        
        self.logger.info(
            "course_generation_started",
            request_id=request_id,
            user_id=user_id,
            transport_method=request.transport_method,
            place_count=len(request.place_ids),
            has_preferences=request.preferences is not None
        )
    
    async def log_generation_completed(
        self,
        request_id: str,
        result: CourseGenerateResponse,
        duration_seconds: float
    ):
        self.metrics.generation_requests.labels(
            transport_method="unknown",  # 결과에서는 정확한 값 추출
            place_count=len(result.course.places),
            status='completed'
        ).inc()
        
        self.metrics.generation_duration.labels(
            transport_method="unknown",
            optimization_method="combined"
        ).observe(duration_seconds)
        
        self.metrics.optimization_score.labels(
            optimization_method="combined"
        ).observe(result.optimization_score)
        
        self.logger.info(
            "course_generation_completed",
            request_id=request_id,
            course_id=result.course_id,
            optimization_score=result.optimization_score,
            generation_time_ms=result.generation_time_ms,
            total_duration=result.course.total_duration,
            total_distance=result.course.total_distance,
            alternatives_count=len(result.alternatives or [])
        )
```

---

## 11. 테스트 전략

### 11-1. 단위 테스트 (TDD)
```python
class TestCourseOptimizer:
    @pytest.fixture
    def sample_places(self):
        return [
            Place(id="cafe_1", name="스타벅스", latitude=37.5665, longitude=126.9780, category="cafe"),
            Place(id="restaurant_1", name="한식당", latitude=37.5675, longitude=126.9790, category="restaurant"),
            Place(id="tourist_1", name="경복궁", latitude=37.5788, longitude=126.9770, category="tourist")
        ]
    
    @pytest.fixture
    def genetic_optimizer(self):
        config = OptimizationConfig(
            population_size=20,
            generations=50,
            mutation_rate=0.1,
            crossover_rate=0.8
        )
        return GeneticOptimizer(config)
    
    async def test_genetic_algorithm_basic_optimization(self, genetic_optimizer, sample_places):
        # Given
        constraints = Constraints(
            max_total_duration=480,  # 8 hours
            transport_method=TransportMethod.WALKING,
            start_time=time(10, 0)
        )
        
        # When
        result = genetic_optimizer.optimize(sample_places, constraints)
        
        # Then
        assert len(result.order) == len(sample_places)
        assert all(0 <= idx < len(sample_places) for idx in result.order)
        assert len(set(result.order)) == len(sample_places)  # 모든 장소가 unique
        assert result.fitness_score > 0.0
    
    async def test_distance_optimization_improvement(self, genetic_optimizer, sample_places):
        # Given
        constraints = Constraints(max_total_duration=480, transport_method=TransportMethod.WALKING)
        random_order = list(range(len(sample_places)))
        random.shuffle(random_order)
        
        # When
        optimized_result = genetic_optimizer.optimize(sample_places, constraints)
        random_distance = calculate_total_distance(sample_places, random_order)
        optimized_distance = calculate_total_distance(sample_places, optimized_result.order)
        
        # Then
        assert optimized_distance < random_distance
        improvement_rate = (random_distance - optimized_distance) / random_distance
        assert improvement_rate >= 0.15  # 최소 15% 개선
    
    async def test_business_hours_constraint(self, genetic_optimizer):
        # Given
        places_with_hours = [
            Place(id="morning_cafe", name="모닝카페", 
                  business_hours=BusinessHours(open_time=time(8, 0), close_time=time(15, 0))),
            Place(id="lunch_restaurant", name="점심식당",
                  business_hours=BusinessHours(open_time=time(11, 0), close_time=time(22, 0))),
            Place(id="evening_bar", name="저녁바",
                  business_hours=BusinessHours(open_time=time(18, 0), close_time=time(2, 0)))
        ]
        constraints = Constraints(start_time=time(9, 0))
        
        # When
        result = genetic_optimizer.optimize(places_with_hours, constraints)
        course_timeline = generate_course_timeline(places_with_hours, result.order, constraints)
        
        # Then
        for place_visit in course_timeline:
            place = next(p for p in places_with_hours if p.id == place_visit.place_id)
            assert place.business_hours.is_open_at(place_visit.arrival_time)
    
    def test_category_diversity_scoring(self):
        # Given
        diverse_arrangement = [0, 1, 2]  # cafe, restaurant, tourist
        monotonous_arrangement = [0, 0, 1]  # cafe, cafe, restaurant (가정)
        
        places = [
            Place(id="1", category="cafe"),
            Place(id="2", category="restaurant"), 
            Place(id="3", category="tourist")
        ]
        
        # When
        diverse_score = calculate_category_diversity(places, diverse_arrangement)
        monotonous_score = calculate_category_diversity(places, monotonous_arrangement)
        
        # Then
        assert diverse_score > monotonous_score
        assert diverse_score >= 0.8  # 높은 다양성 점수
        assert monotonous_score <= 0.6  # 낮은 다양성 점수
```

### 11-2. 통합 테스트
```python
class TestCourseGenerationIntegration:
    @pytest.mark.integration
    async def test_end_to_end_course_generation(self, test_client, postgresql, redis_client):
        # Given
        # 테스트용 장소 데이터 준비
        test_places = await setup_test_places(postgresql)
        user_id = "test_user_123"
        
        request_data = {
            "place_ids": [place.id for place in test_places[:4]],
            "transport_method": "walking",
            "start_time": "10:00",
            "preferences": {
                "max_total_duration": 480,
                "avoid_rush_hours": True
            }
        }
        
        # When
        response = await test_client.post(
            "/api/v1/courses/generate",
            json=request_data,
            headers={"Authorization": f"Bearer {get_test_token(user_id)}"}
        )
        
        # Then
        assert response.status_code == 200
        result = response.json()
        
        assert "course_id" in result
        assert "course" in result
        assert result["optimization_score"] > 0.0
        assert result["generation_time_ms"] < 15000  # 15초 이내
        
        course = result["course"]
        assert len(course["places"]) == 4
        assert course["total_duration"] <= 480  # 제약 조건 준수
        assert course["total_distance"] > 0
        
        # 시간 순서 검증
        for i in range(len(course["places"]) - 1):
            current_departure = datetime.strptime(course["places"][i]["departure_time"], "%H:%M")
            next_arrival = datetime.strptime(course["places"][i+1]["arrival_time"], "%H:%M")
            assert current_departure <= next_arrival
    
    @pytest.mark.integration  
    async def test_course_editing_updates_correctly(self, test_client, postgresql):
        # Given - 먼저 코스를 생성
        initial_course = await create_test_course(test_client)
        course_id = initial_course["course_id"]
        
        edit_request = {
            "course_id": course_id,
            "modifications": [
                {
                    "type": "reorder",
                    "place_id": initial_course["course"]["places"][0]["place_id"],
                    "new_order": 2
                },
                {
                    "type": "change_duration",
                    "place_id": initial_course["course"]["places"][1]["place_id"],
                    "new_stay_duration": 120  # 2시간으로 변경
                }
            ]
        }
        
        # When
        response = await test_client.post(
            f"/api/v1/courses/{course_id}/edit",
            json=edit_request
        )
        
        # Then
        assert response.status_code == 200
        result = response.json()
        
        updated_course = result["updated_course"]
        
        # 순서 변경 확인
        assert updated_course["places"][2]["place_id"] == initial_course["course"]["places"][0]["place_id"]
        
        # 체류시간 변경 확인
        modified_place = next(p for p in updated_course["places"] 
                            if p["place_id"] == initial_course["course"]["places"][1]["place_id"])
        assert modified_place["stay_duration"] == 120
        
        # 영향 분석 확인
        impact = result["impact_analysis"]
        assert "time_change" in impact
        assert "affected_places" in impact
```

### 11-3. 성능 테스트
```python
class TestCourseGenerationPerformance:
    @pytest.mark.performance
    async def test_generation_speed_under_load(self, test_client):
        """동시 요청 처리 성능 테스트"""
        
        # Given
        concurrent_requests = 50
        request_data = {
            "place_ids": ["place_1", "place_2", "place_3", "place_4"],
            "transport_method": "walking"
        }
        
        # When
        start_time = time.time()
        
        async def make_request():
            response = await test_client.post("/api/v1/courses/generate", json=request_data)
            return response.status_code, response.json()
        
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Then
        successful_requests = [r for r in results if not isinstance(r, Exception) and r[0] == 200]
        success_rate = len(successful_requests) / concurrent_requests
        
        assert success_rate >= 0.95  # 95% 이상 성공률
        assert total_duration < 60  # 1분 이내 완료
        
        # 개별 응답 시간 확인
        for status_code, response_data in successful_requests:
            if not isinstance(response_data, Exception):
                assert response_data.get("generation_time_ms", 0) < 15000  # 15초 이내
    
    @pytest.mark.performance
    async def test_optimization_algorithm_convergence(self):
        """최적화 알고리즘 수렴 성능 테스트"""
        
        # Given
        large_place_set = generate_test_places(count=10)  # 10개 장소
        optimizer = GeneticOptimizer(OptimizationConfig(
            population_size=100,
            generations=200,
            mutation_rate=0.1,
            crossover_rate=0.8
        ))
        
        constraints = Constraints(max_total_duration=600, transport_method=TransportMethod.WALKING)
        
        # When
        start_time = time.time()
        result = optimizer.optimize(large_place_set, constraints)
        optimization_time = time.time() - start_time
        
        # Then
        assert optimization_time < 30  # 30초 이내 최적화 완료
        assert result.fitness_score > 0.7  # 높은 품질의 해
        
        # 수렴도 검사 - 여러 번 실행해서 일관된 품질 확인
        multiple_results = []
        for _ in range(5):
            multiple_results.append(optimizer.optimize(large_place_set, constraints))
        
        scores = [r.fitness_score for r in multiple_results]
        score_variance = np.var(scores)
        assert score_variance < 0.05  # 낮은 분산 (안정적 수렴)
```

---

## 12. 배포 및 운영

### 12-1. Docker 컨테이너화
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 최적화 모델 사전 로드
RUN python -c "import numpy as np; import scipy.optimize"

# Health check
COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 12-2. Kubernetes 배포
```yaml
# course-generation-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: course-generation-service
  labels:
    app: course-generation
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: course-generation
  template:
    metadata:
      labels:
        app: course-generation
    spec:
      containers:
      - name: course-generation
        image: hotly/course-generation:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: url
        - name: KAKAO_API_KEY
          valueFrom:
            secretKeyRef:
              name: kakao-secret
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: course-generation-service
spec:
  selector:
    app: course-generation
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: course-generation-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: course-generation-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 13. 용어 사전 (Technical)
- **Genetic Algorithm:** 생물학적 진화를 모방한 최적화 알고리즘
- **Simulated Annealing:** 금속 열처리 과정을 모방한 확률적 최적화 기법
- **Route Matrix:** 모든 장소 쌍 간의 이동시간/거리 정보를 담은 행렬
- **Fitness Score:** 유전 알고리즘에서 개체의 적합도를 나타내는 점수
- **Collaborative Filtering:** 유사 사용자의 선호도를 기반으로 추천하는 기법
- **TTL (Time To Live):** 캐시 데이터의 유효 기간

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 03-course-recommendation 버전과 연동