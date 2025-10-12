# 멀티모달 콘텐츠 분석 시스템 구현 문서

## 📋 개요

PRD 12-multimodal 및 TRD 12-multimodal에 따라 구현된 멀티모달 콘텐츠 분석 시스템입니다.
이미지, 텍스트, 비디오(향후)를 통합 분석하여 장소 정보 추출 정확도를 향상시킵니다.

**구현 날짜**: 2025-01-XX
**Phase**: Phase 1 (이미지 처리 + 멀티모달 분석기)

---

## 🏗️ 아키텍처

### 전체 파이프라인

```
ContentMetadata (입력)
    ↓
MultimodalOrchestrator (조율자)
    ├─→ ImageProcessor (이미지 다운로드 + 전처리)
    │       ├─ httpx 비동기 다운로드
    │       ├─ PIL.Image 변환
    │       ├─ 리사이징 (1024px)
    │       └─ RGB 정규화
    │
    ├─→ TextProcessor (텍스트 정제)
    │       ├─ 해시태그 추출
    │       ├─ 키워드 추출
    │       └─ 위치 힌트 추출
    │
    └─→ GeminiAnalyzerV2 (AI 분석)
            ├─ 멀티모달 프롬프트 생성
            ├─ Gemini 2.0 Flash API 호출
            └─ JSON 응답 파싱
    ↓
PlaceAnalysisResponse (출력 + MultimodalAnalysisMetadata)
```

---

## 📂 구현된 모듈

### 1. **Schemas** (`app/schemas/`)

#### `media.py` - 미디어 처리 스키마
```python
- ImageMetadata: 이미지 메타데이터 (크기, 포맷, EXIF, 품질)
- ProcessedImage: 처리된 이미지 정보
- VideoFrameMetadata: 비디오 프레임 메타데이터 (Phase 2)
- ProcessedMedia: 전체 미디어 처리 결과
```

#### `ai.py` 확장 - 멀티모달 메타데이터
```python
- MultimodalAnalysisMetadata: 분석 메타데이터
    - 처리 시간 분해 (이미지 다운로드, 처리, AI 추론)
    - 품질 메트릭 (이미지 품질, 텍스트 품질)
    - 신뢰도 요인 (confidence_factors)
    - AI 추론 설명 (reasoning)
```

### 2. **Media Services** (`app/services/media/`)

#### `image_processor.py` - 이미지 처리기
**핵심 기능:**
- ✅ 비동기 이미지 다운로드 (httpx + 세마포어로 동시성 제어)
- ✅ PIL.Image 변환 및 검증
- ✅ 자동 리사이징 (1024px, Gemini 권장 크기)
- ✅ 포맷 정규화 (RGBA→RGB, P→RGB)
- ✅ 이미지 품질 점수 계산
- ✅ EXIF 메타데이터 추출 (GPS, 촬영 시간)

**설정:**
```python
MAX_IMAGE_SIZE_MB = 10
TARGET_MAX_DIMENSION = 1024
DOWNLOAD_TIMEOUT = 10 seconds
MAX_CONCURRENT_DOWNLOADS = 3
```

**사용 예시:**
```python
async with ImageProcessor() as processor:
    pil_images, processed_images = await processor.download_and_process_images(
        image_urls=["https://..."],
        max_images=3
    )
```

#### `text_processor.py` - 텍스트 처리기
**핵심 기능:**
- ✅ 텍스트 정제 (공백, 특수문자 제거)
- ✅ 해시태그 추출 (`#태그`)
- ✅ 키워드 추출 (간단한 토큰화)
- ✅ 위치 힌트 추출 (한국 지명 패턴 인식)

### 3. **AI Services** (`app/services/ai/`)

#### `gemini_analyzer_v2.py` - 멀티모달 AI 분석기
**기존 GeminiAnalyzer 대비 개선점:**
- ✅ PIL.Image 객체 직접 전달 (URL → PIL.Image 변환 완료)
- ✅ 멀티모달 최적화 프롬프트
- ✅ 신뢰도 요인 분석
- ✅ 상세한 메타데이터 수집

**API 모델:**
- `gemini-2.0-flash-exp` (빠르고 비용 효율적, 비전 지원)

**주요 메서드:**
```python
async def analyze_multimodal_content(
    request: PlaceAnalysisRequest,
    pil_images: Optional[List[Image.Image]] = None
) -> Tuple[PlaceInfo, MultimodalAnalysisMetadata]
```

#### `prompts/multimodal_prompt.py` - 멀티모달 프롬프트
**프롬프트 설계 원칙:**
1. **이미지 우선**: 이미지에서 읽은 정보가 텍스트보다 우선
2. **사실만 추출**: 추측 금지, 명확한 증거만
3. **불확실하면 null**: 잘못된 정보보다 누락이 나음
4. **JSON만 반환**: 설명 없이 구조화된 JSON만

**동적 지침:**
- 이미지 개수에 따라 분석 지침 조정
- 1장: 간판/상호명 중점 분석
- 여러 장: 교차 검증 및 일관성 확인

### 4. **Orchestrator** (`app/services/places/`)

#### `multimodal_orchestrator.py` - 멀티모달 조율자
**책임:**
1. 미디어 처리 조율 (이미지, 비디오, 텍스트)
2. AI 분석 호출
3. 결과 통합 및 신뢰도 계산
4. Fallback 전략 실행 (이미지 실패 시 텍스트로 진행)

**신뢰도 계산:**
```python
final_confidence = base_confidence (AI)
                 + multimodal_bonus (이미지/비디오 개수)
                 + text_bonus (텍스트 품질)
```

#### `place_analysis_service.py` - 통합 서비스 (업데이트)
**변경 사항:**
- ❌ 기존: `GeminiAnalyzer` 직접 사용 (이미지 URL만 전달)
- ✅ 신규: `MultimodalOrchestrator` 사용 (실제 이미지 다운로드/처리)

**새로운 파라미터:**
- `enable_image_analysis`: 이미지 분석 활성화 (기본: True)
- `max_images`: 최대 처리 이미지 수 (기본: 3)

---

## 🧪 테스트

### Unit Tests

#### `tests/unit/services/media/test_image_processor.py`
**테스트 커버리지:**
- ✅ 이미지 다운로드 및 처리 성공
- ✅ max_images 제한
- ✅ 빈 이미지 리스트
- ✅ 이미지 크기 검증 (너무 크거나 작음)
- ✅ 포맷 검증
- ✅ 리사이징 로직
- ✅ RGBA→RGB 변환
- ✅ 품질 점수 계산
- ✅ 전체 파이프라인 통합 테스트

#### `tests/unit/services/test_multimodal_integration.py`
**통합 테스트:**
- ✅ 이미지 포함 콘텐츠 분석
- ✅ 텍스트 전용 분석
- ✅ 에러 핸들링
- ✅ Fallback 동작

### 테스트 실행
```bash
cd backend
poetry run pytest tests/unit/services/media/ -v
poetry run pytest tests/unit/services/test_multimodal_integration.py -v
```

---

## 📊 성능 최적화

### 이미지 처리 최적화
1. **동시성 제어**: Semaphore(3)로 최대 3개 이미지 동시 다운로드
2. **타임아웃**: 10초 다운로드 타임아웃
3. **크기 제한**: 10MB 최대 크기, 1024px 리사이징
4. **실패 허용**: 개별 이미지 실패 시 계속 진행 (전체 실패 방지)

### AI 분석 최적화
1. **낮은 temperature**: 0.1 (일관성 있는 출력)
2. **재시도 로직**: 지수 백오프 (1초 → 2초 → 4초)
3. **Rate limit 처리**: RateLimitError 시 자동 재시도

---

## 🔧 사용 방법

### 기본 사용
```python
from app.services.places.place_analysis_service import PlaceAnalysisService
from app.schemas.content import ContentMetadata

service = PlaceAnalysisService()

content = ContentMetadata(
    title="서울 성수동 감성 카페",
    description="북유럽 감성의 브런치 카페",
    hashtags=["성수동", "카페", "브런치"],
    images=["https://example.com/cafe.jpg"],
)

response = await service.analyze_content(
    content,
    enable_image_analysis=True,
    max_images=3
)

if response.success:
    print(f"장소: {response.place_info.name}")
    print(f"신뢰도: {response.confidence}")
    print(f"이미지 분석 개수: {response.multimodal_metadata.num_images_analyzed}")
```

### 텍스트 전용 분석
```python
response = await service.analyze_content(
    content,
    enable_image_analysis=False  # 이미지 다운로드 생략
)
```

---

## 🚀 향후 계획 (Phase 2 & 3)

### Phase 2: 비디오 프레임 분석
- [ ] YouTube 영상에서 핵심 프레임 추출
- [ ] 자막/캡션 텍스트 추출
- [ ] 프레임 품질 평가
- [ ] 비디오 메타데이터 통합

### Phase 3: 고급 최적화
- [ ] 배치 처리 (여러 콘텐츠 동시 분석)
- [ ] 지능형 캐싱 (이미지 처리 결과 캐싱)
- [ ] A/B 테스트 프레임워크
- [ ] 성능 모니터링 대시보드

---

## 📝 의존성

### 새로운 의존성
```toml
[tool.poetry.dependencies]
httpx = "^0.24.0"           # 비동기 HTTP 클라이언트
Pillow = "^10.0.0"          # 이미지 처리
google-generativeai = "^0.3.0"  # Gemini API
```

### 기존 의존성
- FastAPI, Pydantic, asyncio (기존 사용)

---

## ⚠️ 주의사항

1. **API 키 필수**: `GEMINI_API_KEY` 환경 변수 설정 필요
2. **Rate Limit**: Gemini API 할당량 모니터링 필요
3. **이미지 크기**: 10MB 제한, 초과 시 에러
4. **네트워크 의존성**: 이미지 다운로드 실패 시 텍스트로 fallback
5. **동시성 제한**: 동시 분석 요청 시 세마포어로 제어

---

## 📚 참고 문서

- [PRD 12-multimodal](../../prd/12-multimodal.md)
- [TRD 12-multimodal](../../trd/12-multimodal.md)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [PIL/Pillow Documentation](https://pillow.readthedocs.io/)

---

## 👥 기여자

- 구현: Claude Code Agent
- 리뷰: [TBD]
- 테스트: [TBD]
