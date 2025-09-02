# TRD: SNS 링크 분석 및 장소 정보 추출

## 1. 기술 개요
**목적:** PRD 01-sns-link-analysis 요구사항을 충족하기 위한 기술적 구현 방안 및 아키텍처 설계

**핵심 기술 스택:**
- AI/ML: Google Gemini API (멀티모달 분석)
- 웹 스크래핑: Playwright + BeautifulSoup4
- 캐시: Redis (분산 캐싱)
- 큐: RabbitMQ (비동기 처리)
- API: FastAPI + Pydantic

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Mobile App] 
    ↓ POST /api/v1/links/analyze
[API Gateway + Rate Limiter]
    ↓
[FastAPI Service]
    ↓ (캐시 조회)
[Redis Cache] 
    ↓ (캐시 미스 시)
[Analysis Queue] → [Worker Processes]
    ↓
[Content Scraper] → [AI Analyzer] → [Data Validator]
    ↓
[PostgreSQL] + [Cache Update]
```

### 2-2. 마이크로서비스 분리
```
1. Link Analysis Service
   - URL 검증 및 전처리
   - 캐시 조회/관리
   - 결과 집계

2. Content Extraction Service  
   - SNS 플랫폼별 스크래핑
   - 메타데이터 추출
   - 이미지/텍스트 정규화

3. AI Processing Service
   - Gemini API 연동
   - 프롬프트 최적화
   - 결과 후처리

4. Cache Management Service
   - Redis 클러스터 관리
   - TTL 정책 적용
   - 캐시 무효화
```

---

## 3. API 설계

### 3-1. 링크 분석 요청
```python
# Request Schema
class LinkAnalyzeRequest(BaseModel):
    url: str = Field(..., regex=r'^https?://')
    user_id: Optional[str] = None
    priority: Priority = Priority.NORMAL
    callback_url: Optional[str] = None

# Response Schema  
class LinkAnalyzeResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    cache_hit: bool
    estimated_time: Optional[int] = None
    places: Optional[List[PlaceInfo]] = None
```

### 3-2. 결과 조회
```python
class PlaceInfo(BaseModel):
    place_name: str
    address: Optional[str] = None
    category: List[str] = []
    business_hours: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    coordinates: Optional[Coordinates] = None
    extracted_at: datetime

class AnalysisResult(BaseModel):
    analysis_id: str
    url: str
    status: AnalysisStatus
    places: List[PlaceInfo]
    processing_time: float
    cache_hit: bool
    error_message: Optional[str] = None
```

---

## 4. 데이터베이스 설계

### 4-1. PostgreSQL 스키마
```sql
-- analyses 테이블
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id VARCHAR(255) NOT NULL UNIQUE,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL UNIQUE,
    user_id UUID NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    places JSONB NOT NULL DEFAULT '[]',
    processing_time DECIMAL(10,3) NULL,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days')
);

-- 인덱스 정의
CREATE UNIQUE INDEX idx_analyses_url_hash ON analyses(url_hash);
CREATE INDEX idx_analyses_user_created ON analyses(user_id, created_at DESC);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_expires ON analyses(expires_at);

-- 만료된 레코드 자동 삭제 (pg_cron 확장 필요)
-- SELECT cron.schedule('cleanup-expired-analyses', '0 */6 * * *', 
--   'DELETE FROM analyses WHERE expires_at < NOW()');

-- places JSONB 구조 예시
/*
{
  "place_name": "string",
  "address": "string|null",
  "category": ["string"],
  "business_hours": "string|null", 
  "image_url": "string|null",
  "description": "string|null",
  "confidence": number,
  "coordinates": {
    "lat": number,
    "lng": number
  }
}
*/
```

### 4-2. Redis 캐시 구조
```
키 패턴:
- hotly:link_analysis:{url_hash} → 분석 결과 (TTL: 7일)
- hotly:analysis_status:{analysis_id} → 처리 상태 (TTL: 1시간)
- hotly:rate_limit:{user_id} → API 호출 제한 (TTL: 1분)
- hotly:popular_links → 인기 링크 집합 (Sorted Set)
```

---

## 5. AI 분석 시스템

### 5-1. Gemini API 연동
```python
class GeminiAnalyzer:
    def __init__(self):
        self.client = genai.GenerativeModel('gemini-pro-vision')
        self.prompt_template = self._load_prompt_template()
    
    async def analyze_content(self, text: str, images: List[str]) -> AnalysisResult:
        prompt = self.prompt_template.format(
            content_text=text,
            instruction="장소 정보를 JSON 형태로 추출하세요"
        )
        
        try:
            response = await self.client.generate_content([
                prompt,
                *[Image.open(img) for img in images]
            ])
            
            return self._parse_response(response.text)
        
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise AnalysisError(f"AI 분석 실패: {str(e)}")
```

### 5-2. 프롬프트 엔지니어링
```
시스템 프롬프트:
"""
당신은 SNS 콘텐츠에서 장소 정보를 추출하는 전문가입니다.
주어진 텍스트와 이미지에서 다음 정보를 추출하세요:

1. 장소명 (필수)
2. 주소 (가능한 경우)
3. 카테고리 (카페, 맛집, 관광지 등)
4. 영업시간 (명시된 경우)
5. 특징/설명 (50자 이내)

출력 형식:
{
  "places": [
    {
      "place_name": "정확한 장소명",
      "address": "상세 주소 또는 null",
      "category": ["카테고리1", "카테고리2"],
      "business_hours": "영업시간 또는 null",
      "description": "간단한 설명",
      "confidence": 0.95
    }
  ]
}

신뢰도 기준:
- 0.9+: 장소명과 주소 모두 명확
- 0.7-0.9: 장소명 명확, 주소 추정
- 0.5-0.7: 장소명 추정, 주소 불명확
- 0.5 미만: 정보 부족으로 제외
"""
```

---

## 6. 콘텐츠 추출 시스템

### 6-1. SNS 플랫폼별 스크래퍼
```python
class ContentExtractor:
    def __init__(self):
        self.scrapers = {
            'instagram.com': InstagramScraper(),
            'youtube.com': YouTubeScraper(),
            'blog.naver.com': NaverBlogScraper(),
        }
    
    async def extract_content(self, url: str) -> ContentData:
        domain = urlparse(url).netloc
        scraper = self.scrapers.get(domain)
        
        if not scraper:
            raise UnsupportedPlatformError(f"지원하지 않는 플랫폼: {domain}")
        
        return await scraper.extract(url)

class InstagramScraper:
    async def extract(self, url: str) -> ContentData:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # User-Agent 설정으로 봇 감지 회피
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 ...'
            })
            
            await page.goto(url, wait_until='networkidle')
            
            # 메타데이터 추출
            title = await page.locator('meta[property="og:title"]').get_attribute('content')
            description = await page.locator('meta[property="og:description"]').get_attribute('content')
            images = await page.locator('meta[property="og:image"]').all()
            
            return ContentData(
                url=url,
                title=title,
                description=description,
                images=[await img.get_attribute('content') for img in images],
                text_content=await page.inner_text('article'),
                extracted_at=datetime.utcnow()
            )
```

### 6-2. 콘텐츠 정규화
```python
class ContentNormalizer:
    def normalize(self, content: ContentData) -> ContentData:
        # 텍스트 정제
        clean_text = self._clean_text(content.text_content)
        
        # 이미지 URL 검증 및 다운로드
        valid_images = self._validate_images(content.images)
        
        # 메타데이터 보강
        enhanced_content = self._enhance_metadata(content)
        
        return ContentData(
            url=content.url,
            title=enhanced_content.title,
            description=clean_text,
            images=valid_images,
            text_content=clean_text,
            extracted_at=content.extracted_at
        )
    
    def _clean_text(self, text: str) -> str:
        # 해시태그, 멘션 정리
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        
        # 이모지 제거 또는 변환
        text = emoji.demojize(text)
        
        # 과도한 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
```

---

## 7. 캐싱 전략

### 7-1. 캐시 레이어 설계
```python
class CacheManager:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.local_cache = TTLCache(maxsize=1000, ttl=300)  # 5분
    
    async def get_analysis_result(self, url_hash: str) -> Optional[AnalysisResult]:
        # L1: 로컬 캐시
        result = self.local_cache.get(url_hash)
        if result:
            return result
        
        # L2: Redis 캐시
        cached = await self.redis.get(f"hotly:link_analysis:{url_hash}")
        if cached:
            result = AnalysisResult.parse_raw(cached)
            self.local_cache[url_hash] = result
            return result
        
        return None
    
    async def set_analysis_result(self, url_hash: str, result: AnalysisResult):
        # L1 + L2 동시 저장
        self.local_cache[url_hash] = result
        await self.redis.setex(
            f"hotly:link_analysis:{url_hash}",
            timedelta(days=7),
            result.json()
        )
```

### 7-2. 캐시 무효화 전략
```python
class CacheInvalidator:
    async def invalidate_url(self, url: str):
        url_hash = self._generate_hash(url)
        await self.redis.delete(f"hotly:link_analysis:{url_hash}")
    
    async def invalidate_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
    
    async def scheduled_cleanup(self):
        """매일 실행되는 캐시 정리"""
        # 오래된 분석 결과 정리
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        async with self.db.begin() as conn:
            await conn.execute(
                text("DELETE FROM analyses WHERE created_at < :cutoff_date AND status IN ('completed', 'failed')"),
                {"cutoff_date": cutoff_date}
            )
```

---

## 8. 비동기 처리

### 8-1. 작업 큐 설계
```python
# Celery 작업 정의
@celery_app.task(bind=True, max_retries=3)
def analyze_link_task(self, analysis_id: str, url: str, user_id: Optional[str]):
    try:
        # 분석 상태 업데이트
        update_analysis_status(analysis_id, AnalysisStatus.PROCESSING)
        
        # 콘텐츠 추출
        extractor = ContentExtractor()
        content = await extractor.extract_content(url)
        
        # AI 분석
        analyzer = GeminiAnalyzer()
        result = await analyzer.analyze_content(
            content.text_content, 
            content.images
        )
        
        # 결과 저장
        await save_analysis_result(analysis_id, result)
        
        # 캐시 업데이트
        cache_manager = CacheManager()
        await cache_manager.set_analysis_result(
            generate_url_hash(url), 
            result
        )
        
    except Exception as exc:
        logger.error(f"Analysis failed for {analysis_id}: {exc}")
        update_analysis_status(analysis_id, AnalysisStatus.FAILED, str(exc))
        
        # 재시도 로직
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
```

### 8-2. 우선순위 큐
```python
class PriorityQueue:
    def __init__(self):
        self.queues = {
            Priority.HIGH: 'hotly.analysis.high',
            Priority.NORMAL: 'hotly.analysis.normal', 
            Priority.LOW: 'hotly.analysis.low'
        }
    
    async def enqueue(self, task_data: dict, priority: Priority):
        queue_name = self.queues[priority]
        await celery_app.send_task(
            'analyze_link_task',
            args=[task_data],
            queue=queue_name,
            priority=priority.value
        )
```

---

## 9. 에러 처리 및 복원력

### 9-1. 예외 처리 계층
```python
# 도메인 예외 정의
class AnalysisError(Exception):
    """분석 관련 기본 예외"""
    pass

class UnsupportedPlatformError(AnalysisError):
    """지원하지 않는 플랫폼"""
    pass

class ContentExtractionError(AnalysisError):
    """콘텐츠 추출 실패"""
    pass

class AIAnalysisError(AnalysisError):
    """AI 분석 실패"""
    pass

# HTTP 예외 매핑
@app.exception_handler(AnalysisError)
async def analysis_error_handler(request: Request, exc: AnalysisError):
    error_code = {
        UnsupportedPlatformError: "UNSUPPORTED_PLATFORM",
        ContentExtractionError: "CONTENT_EXTRACTION_FAILED",
        AIAnalysisError: "AI_ANALYSIS_FAILED",
    }.get(type(exc), "ANALYSIS_ERROR")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": error_code,
                "message": str(exc),
                "details": {
                    "retry_after": 60 if isinstance(exc, AIAnalysisError) else None
                }
            }
        }
    )
```

### 9-2. Circuit Breaker 패턴
```python
class GeminiCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Gemini API circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 10. 모니터링 및 로깅

### 10-1. 구조화 로깅
```python
import structlog

logger = structlog.get_logger()

async def analyze_link(url: str, user_id: str):
    analysis_id = generate_analysis_id()
    
    logger.info(
        "link_analysis_started",
        analysis_id=analysis_id,
        url_hash=generate_url_hash(url),
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    try:
        start_time = time.time()
        result = await _perform_analysis(url)
        processing_time = time.time() - start_time
        
        logger.info(
            "link_analysis_completed",
            analysis_id=analysis_id,
            processing_time=processing_time,
            places_found=len(result.places),
            cache_hit=result.cache_hit
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "link_analysis_failed",
            analysis_id=analysis_id,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc()
        )
        raise
```

### 10-2. 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
analysis_requests_total = Counter(
    'analysis_requests_total',
    'Total number of analysis requests',
    ['platform', 'status']
)

analysis_duration_seconds = Histogram(
    'analysis_duration_seconds',
    'Time spent on analysis',
    ['platform', 'cache_hit']
)

active_analyses_gauge = Gauge(
    'active_analyses_current',
    'Current number of active analyses'
)

# 메트릭 수집
class MetricsCollector:
    def record_analysis_request(self, platform: str, status: str):
        analysis_requests_total.labels(platform=platform, status=status).inc()
    
    def record_analysis_duration(self, platform: str, duration: float, cache_hit: bool):
        analysis_duration_seconds.labels(
            platform=platform,
            cache_hit=cache_hit
        ).observe(duration)
    
    def update_active_analyses(self, count: int):
        active_analyses_gauge.set(count)
```

---

## 11. 보안 및 개인정보 보호

### 11-1. 입력 검증 및 보안
```python
class URLValidator:
    ALLOWED_DOMAINS = {
        'instagram.com', 'www.instagram.com',
        'youtube.com', 'www.youtube.com', 'youtu.be',
        'blog.naver.com'
    }
    
    def validate(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            
            # 프로토콜 검사
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError("HTTP/HTTPS URL만 지원됩니다")
            
            # 도메인 허용 목록 검사
            if parsed.netloc not in self.ALLOWED_DOMAINS:
                raise ValidationError(f"지원하지 않는 도메인: {parsed.netloc}")
            
            # URL 길이 제한
            if len(url) > 2048:
                raise ValidationError("URL 길이가 너무 깁니다")
            
            return True
            
        except Exception as e:
            raise ValidationError(f"유효하지 않은 URL: {str(e)}")

# Rate Limiting
class RateLimiter:
    async def check_rate_limit(self, user_id: str) -> bool:
        key = f"hotly:rate_limit:{user_id}"
        current = await redis.get(key)
        
        if current and int(current) >= settings.MAX_REQUESTS_PER_MINUTE:
            raise RateLimitExceededError("분당 요청 한도를 초과했습니다")
        
        await redis.incr(key)
        await redis.expire(key, 60)
        return True
```

### 11-2. 개인정보 마스킹
```python
class DataMasker:
    def mask_sensitive_data(self, content: str) -> str:
        # 전화번호 마스킹
        content = re.sub(
            r'\b(\d{3})-(\d{4})-(\d{4})\b',
            r'\1-****-\4',
            content
        )
        
        # 이메일 마스킹
        content = re.sub(
            r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'****@\2',
            content
        )
        
        return content
    
    def should_store_content(self, content: ContentData) -> bool:
        """개인정보 포함 여부 확인"""
        sensitive_patterns = [
            r'\b\d{3}-\d{4}-\d{4}\b',  # 전화번호
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 이메일
            r'\b\d{6}-\d{7}\b',  # 주민번호
        ]
        
        text = content.text_content + ' ' + (content.description or '')
        
        for pattern in sensitive_patterns:
            if re.search(pattern, text):
                return False  # 개인정보 포함으로 저장 안함
        
        return True
```

---

## 12. 성능 최적화

### 12-1. 동시성 처리
```python
import asyncio
from aiohttp import ClientSession

class ConcurrentAnalyzer:
    def __init__(self, max_concurrent=10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
    
    async def analyze_multiple(self, urls: List[str]) -> List[AnalysisResult]:
        async with ClientSession() as session:
            self.session = session
            tasks = [self._analyze_single(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _analyze_single(self, url: str) -> AnalysisResult:
        async with self.semaphore:
            return await self.analyze_link(url)
```

### 12-2. 배치 처리 최적화
```python
class BatchProcessor:
    def __init__(self, batch_size=50, timeout=300):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending_requests = []
    
    async def process_batch(self):
        if len(self.pending_requests) >= self.batch_size:
            batch = self.pending_requests[:self.batch_size]
            self.pending_requests = self.pending_requests[self.batch_size:]
            
            # 배치로 AI API 호출 (비용 절약)
            results = await self._batch_analyze(batch)
            
            # 개별 결과 처리
            for req, result in zip(batch, results):
                await self._update_individual_result(req, result)
    
    async def _batch_analyze(self, batch: List[AnalysisRequest]) -> List[AnalysisResult]:
        # Gemini API 배치 호출
        prompt = self._create_batch_prompt(batch)
        response = await self.gemini_client.generate_content(prompt)
        return self._parse_batch_response(response, len(batch))
```

---

## 13. 테스트 전략

### 13-1. 단위 테스트 (TDD)
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestLinkAnalyzer:
    @pytest.fixture
    async def analyzer(self):
        return LinkAnalyzer(
            gemini_client=AsyncMock(),
            cache_manager=AsyncMock(),
            content_extractor=AsyncMock()
        )
    
    async def test_analyze_instagram_link_success(self, analyzer):
        # Given
        url = "https://www.instagram.com/p/test123/"
        expected_place = PlaceInfo(
            place_name="테스트 카페",
            address="서울시 강남구",
            category=["카페"],
            confidence=0.95
        )
        
        analyzer.content_extractor.extract_content.return_value = ContentData(
            url=url,
            text_content="테스트 카페에서 좋은 시간 보냈어요! #카페 #강남",
            images=["https://example.com/image.jpg"]
        )
        
        analyzer.gemini_client.analyze_content.return_value = AnalysisResult(
            places=[expected_place]
        )
        
        # When
        result = await analyzer.analyze_link(url)
        
        # Then
        assert result.places[0].place_name == "테스트 카페"
        assert result.places[0].confidence >= 0.9
        analyzer.content_extractor.extract_content.assert_called_once_with(url)
```

### 13-2. 통합 테스트
```python
class TestLinkAnalysisIntegration:
    @pytest.mark.integration
    async def test_end_to_end_analysis(self, test_client, redis_client, postgresql):
        # Given
        url = "https://www.instagram.com/p/real_post/"
        
        # When
        response = await test_client.post(
            "/api/v1/links/analyze",
            json={"url": url}
        )
        
        # Then
        assert response.status_code == 202
        analysis_id = response.json()["analysis_id"]
        
        # 비동기 처리 완료 대기
        await asyncio.sleep(5)
        
        # 결과 확인
        result_response = await test_client.get(
            f"/api/v1/analyses/{analysis_id}"
        )
        
        assert result_response.status_code == 200
        result = result_response.json()
        assert result["status"] == "completed"
        assert len(result["places"]) > 0
```

### 13-3. 성능 테스트
```python
class TestPerformance:
    @pytest.mark.performance
    async def test_cache_hit_performance(self, analyzer):
        # Given
        url = "https://www.instagram.com/p/cached_post/"
        
        # 첫 번째 요청 (캐시 미스)
        start_time = time.time()
        result1 = await analyzer.analyze_link(url)
        first_request_time = time.time() - start_time
        
        # 두 번째 요청 (캐시 히트)
        start_time = time.time()
        result2 = await analyzer.analyze_link(url)
        second_request_time = time.time() - start_time
        
        # Then
        assert result2.cache_hit is True
        assert second_request_time < first_request_time / 10  # 10배 이상 빠름
```

---

## 14. 배포 및 운영

### 14-1. Docker 컨테이너화
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Playwright 브라우저 설치
RUN playwright install chromium

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14-2. Kubernetes 배포
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: link-analysis-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: link-analysis
  template:
    metadata:
      labels:
        app: link-analysis
    spec:
      containers:
      - name: link-analysis
        image: hotly/link-analysis:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 15. 용어 사전(Technical)
- **Circuit Breaker:** 외부 서비스 장애 시 연쇄 장애 방지 패턴
- **Content Scraping:** 웹 페이지에서 구조화된 데이터 추출
- **Multimodal AI:** 텍스트와 이미지를 함께 처리하는 AI 모델
- **TTL (Time To Live):** 캐시 데이터의 유효 기간
- **Idempotency:** 동일한 요청을 여러 번 수행해도 결과가 같음을 보장하는 성질

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 01-sns-link-analysis 버전과 연동