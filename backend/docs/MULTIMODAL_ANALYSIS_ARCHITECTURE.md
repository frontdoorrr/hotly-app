# Multimodal Content Analysis Architecture

> 멀티모달 콘텐츠 분석 시스템의 모듈화 설계 문서

## 📋 목차

1. [개요](#개요)
2. [현재 문제점](#현재-문제점)
3. [설계 목표](#설계-목표)
4. [모듈 구조](#모듈-구조)
5. [데이터 흐름](#데이터-흐름)
6. [설계 원칙](#설계-원칙)
7. [구현 로드맵](#구현-로드맵)

---

## 개요

사용자가 제공한 링크(Instagram, Naver Blog, YouTube 등)의 **실제 콘텐츠**를 Gemini AI로 분석하는 시스템입니다.

### 핵심 기능

- 📸 **이미지 분석**: URL에서 이미지 다운로드 → Gemini 비전 분석
- 🎥 **동영상 분석**: 동영상 썸네일/프레임 추출 → 비주얼 분석
- 📝 **텍스트 분석**: 제목, 설명, 해시태그 → 자연어 이해
- 🤖 **멀티모달 통합**: 여러 모달리티를 결합한 종합 장소 정보 추출

---

## 현재 문제점

### 기존 흐름

```
LinkAnalysis API → ContentExtractor → PlaceAnalysisService → GeminiAnalyzer
                    (mock 데이터)      (URL 문자열만)        (이미지 못봄)
```

### 주요 이슈

1. **ContentExtractor**
   - Playwright 의존성 (ImportError 시 mock 데이터 반환)
   - 실제 크롤링 없이 더미 데이터 사용

2. **PlaceAnalysisService**
   - 이미지 URL을 문자열로만 전달
   - Gemini가 실제 이미지를 볼 수 없음

3. **GeminiAnalyzer**
   - PIL.Image 객체를 받을 준비는 되어있음
   - 하지만 실제로는 URL 문자열만 받음

### 결과

```json
{
  "name": "Amazing restaurant",  // ← 더미 데이터
  "category": "restaurant",
  "cached": true
}
```

실제 콘텐츠 분석이 아닌 mock 데이터를 반환하고 있습니다.

---

## 설계 목표

### 🎯 비즈니스 목표

1. **정확한 장소 정보 추출**: 실제 이미지/동영상을 AI가 분석
2. **다양한 입력 지원**: URL, 파일 업로드, 텍스트 등
3. **확장 가능한 구조**: 새로운 미디어 타입/플랫폼 추가 용이
4. **고품질 분석**: 멀티모달 정보를 종합한 신뢰도 높은 결과

### 🏗️ 기술 목표

- **모듈화**: 각 모듈의 책임 명확히 분리
- **테스트 가능성**: 각 모듈을 독립적으로 테스트
- **유지보수성**: 한 모듈 변경이 다른 모듈에 영향 최소화
- **재사용성**: ImageProcessor 등을 다른 기능에서도 사용

---

## 모듈 구조

### 전체 아키텍처

```
사용자 입력 (URL/파일/텍스트)
    ↓
┌─────────────────────┐
│  Content Loader     │  콘텐츠 소스에서 원시 데이터 가져오기
└─────────────────────┘
    ↓
┌─────────────────────┐
│  Media Processor    │  미디어를 AI가 이해할 수 있는 형태로 변환
└─────────────────────┘
    ↓
┌─────────────────────┐
│  Multimodal         │  여러 모달리티를 결합하여 AI 분석
│  Analyzer           │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  Result Builder     │  분석 결과를 비즈니스 객체로 구조화
└─────────────────────┘
    ↓
장소 정보 응답
```

---

## Module 1: Content Loader

### 책임
다양한 소스에서 원시 콘텐츠 가져오기

### 위치
`app/services/content/`

### 구성 요소

#### 1.1 ContentLoader (추상 계층)
```python
# content_loader.py
class ContentLoader:
    """콘텐츠 로딩을 담당하는 추상 계층"""

    async def load_from_url(self, url: str) -> RawContent:
        """URL에서 콘텐츠 로드"""

    async def load_from_file(self, file_path: str) -> RawContent:
        """로컬 파일에서 콘텐츠 로드"""

    async def load_from_upload(self, file: UploadFile) -> RawContent:
        """업로드된 파일에서 콘텐츠 로드"""
```

#### 1.2 URLLoader
```python
# url_loader.py
class URLLoader:
    """URL에서 콘텐츠 로딩"""

    async def load(self, url: str) -> RawContent:
        """
        URL에서 메타데이터와 미디어 URL 추출

        지원 방법:
        - HTTP 요청 + BeautifulSoup (정적 페이지)
        - Open Graph 메타데이터 파싱
        - oEmbed 프로토콜 (YouTube, Instagram)
        - (선택) Playwright (동적 페이지)
        """
```

**주요 기능:**
- Platform 감지 (Instagram, Naver Blog, YouTube 등)
- Open Graph meta tags 추출
- 이미지/동영상 URL 수집
- 텍스트 콘텐츠 추출

#### 1.3 FileLoader
```python
# file_loader.py
class FileLoader:
    """로컬 파일에서 콘텐츠 로딩"""

    async def load(self, file_path: str) -> RawContent:
        """
        지원 파일 타입:
        - 이미지: jpg, png, gif, webp
        - 동영상: mp4, mov, avi
        - 텍스트: txt, json
        """
```

#### 1.4 UploadLoader
```python
# upload_loader.py
class UploadLoader:
    """업로드된 파일 처리"""

    async def load(self, upload: UploadFile) -> RawContent:
        """FastAPI UploadFile 객체 처리"""
```

### 출력 데이터

```python
# schemas/content.py
class RawContent(BaseModel):
    """Content Loader의 출력 데이터"""

    source_type: Literal["url", "file", "upload"]
    source: str  # URL, 파일경로, 또는 파일명

    # 추출된 데이터
    text_content: Optional[str]  # 제목, 설명 등
    image_urls: List[str]        # 이미지 URL 리스트
    video_urls: List[str]        # 동영상 URL 리스트

    # 메타데이터
    metadata: Dict[str, Any]  # platform, hashtags, location 등
    extraction_time: float
```

---

## Module 2: Media Processor

### 책임
미디어를 AI가 이해할 수 있는 형태로 변환

### 위치
`app/services/media/`

### 구성 요소

#### 2.1 ImageProcessor
```python
# image_processor.py
class ImageProcessor:
    """이미지 다운로드 및 전처리"""

    async def download_image(self, url: str) -> PIL.Image:
        """
        이미지 URL → PIL.Image 객체

        - httpx로 비동기 다운로드
        - 타임아웃: 10초
        - 최대 크기: 10MB
        - 포맷 검증 (JPEG, PNG, WebP 등)
        """

    async def resize_image(
        self,
        image: PIL.Image,
        max_size: Tuple[int, int] = (1024, 1024)
    ) -> PIL.Image:
        """
        이미지 리사이즈 (Gemini API 최적화)

        - 종횡비 유지
        - 최대 크기 제한
        """

    async def validate_image(self, image: PIL.Image) -> bool:
        """이미지 유효성 검증"""

    async def extract_metadata(self, image: PIL.Image) -> ImageMetadata:
        """EXIF 메타데이터 추출 (위치, 시간 등)"""
```

**주요 기능:**
- 이미지 다운로드 (URL → PIL.Image)
- 크기 조정 (Gemini API 제한 고려)
- 포맷 변환 (WebP → JPEG 등)
- EXIF 메타데이터 추출

#### 2.2 VideoProcessor
```python
# video_processor.py
class VideoProcessor:
    """동영상 처리 및 프레임 추출"""

    async def extract_thumbnail(self, video_url: str) -> PIL.Image:
        """
        동영상 썸네일 추출

        - YouTube: YouTube API로 썸네일 URL
        - 일반: 첫 프레임 또는 중간 프레임
        """

    async def extract_key_frames(
        self,
        video_url: str,
        num_frames: int = 3
    ) -> List[PIL.Image]:
        """
        동영상에서 주요 프레임 추출

        - 시작, 중간, 끝 프레임
        - 또는 장면 변화 감지
        """

    async def get_youtube_thumbnail(self, video_id: str) -> PIL.Image:
        """YouTube 썸네일 (고해상도)"""

    async def get_youtube_transcript(self, video_id: str) -> Optional[str]:
        """YouTube 자막 추출 (youtube-transcript-api)"""
```

**주요 기능:**
- YouTube 썸네일 추출
- 동영상 프레임 샘플링
- 자막/설명 추출

#### 2.3 TextProcessor
```python
# text_processor.py
class TextProcessor:
    """텍스트 정제 및 추출"""

    async def extract_hashtags(self, text: str) -> List[str]:
        """해시태그 추출 (#맛집, #카페 등)"""

    async def clean_text(self, text: str) -> str:
        """
        텍스트 정제

        - HTML 태그 제거
        - 특수문자 정리
        - 공백 정규화
        """

    async def extract_keywords(self, text: str) -> List[str]:
        """주요 키워드 추출 (한국어 형태소 분석)"""
```

### 출력 데이터

```python
# schemas/media.py
class ProcessedMedia(BaseModel):
    """Media Processor의 출력 데이터"""

    text: str                      # 정제된 텍스트
    images: List[PIL.Image]        # 실제 이미지 객체들
    video_frames: List[PIL.Image]  # 동영상 프레임들

    # 메타데이터
    metadata: MediaMetadata
    processing_time: float

class MediaMetadata(BaseModel):
    """미디어 메타데이터"""

    num_images: int
    num_video_frames: int
    total_size_mb: float
    hashtags: List[str]
    keywords: List[str]
```

---

## Module 3: Multimodal Analyzer

### 책임
여러 모달리티를 결합하여 AI 분석

### 위치
`app/services/ai/`

### 구성 요소

#### 3.1 MultimodalAnalyzer (새)
```python
# multimodal_analyzer.py
class MultimodalAnalyzer:
    """멀티모달 콘텐츠 분석 오케스트레이터"""

    def __init__(self):
        self.gemini = GeminiAnalyzer()
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()

    async def analyze_content(
        self,
        text: Optional[str] = None,
        images: Optional[List[Union[str, PIL.Image]]] = None,
        video: Optional[str] = None
    ) -> AIAnalysisResult:
        """
        텍스트 + 이미지 + 동영상을 종합 분석

        흐름:
        1. 미디어 전처리 (URL → PIL.Image)
        2. Gemini 멀티모달 API 호출
        3. 결과 후처리
        """

        # 1. 이미지 전처리
        processed_images = []
        if images:
            for img in images:
                if isinstance(img, str):  # URL
                    img_obj = await self.image_processor.download_image(img)
                    processed_images.append(img_obj)
                else:  # PIL.Image
                    processed_images.append(img)

        # 2. 동영상 프레임 추출
        video_frames = []
        if video:
            frames = await self.video_processor.extract_key_frames(video)
            video_frames.extend(frames)

        # 3. Gemini API 호출
        result = await self.gemini.analyze_multimodal(
            text=text,
            images=processed_images + video_frames
        )

        return result
```

#### 3.2 GeminiAnalyzer (기존 개선)
```python
# gemini_analyzer.py
class GeminiAnalyzer:
    """Gemini API 전문 클래스"""

    async def analyze_multimodal(
        self,
        text: str,
        images: List[PIL.Image]
    ) -> PlaceInfo:
        """
        이미지를 포함한 멀티모달 분석

        Gemini API에 실제 이미지 객체 전달
        """

        # 프롬프트 구성
        prompt = self._format_prompt(text)

        # Gemini API 호출 (이미 구현된 로직 사용)
        response = await self._call_gemini_api(prompt, images)

        # JSON 파싱 및 검증
        place_data = self._parse_and_validate_response(response)

        return PlaceInfo(**place_data)
```

**개선 사항:**
- 기존 `_call_gemini_api()` 메서드가 이미 PIL.Image 지원
- URL이 아닌 실제 이미지 객체를 전달받도록 변경

### 출력 데이터

```python
# schemas/analysis.py
class AIAnalysisResult(BaseModel):
    """AI Analyzer의 출력 데이터"""

    place_info: PlaceInfo     # 추출된 장소 정보
    confidence: float         # 신뢰도 (0.0 ~ 1.0)
    reasoning: Optional[str]  # AI의 추론 과정
    analysis_time: float
```

---

## Module 4: Result Builder

### 책임
AI 분석 결과를 비즈니스 객체로 구조화

### 위치
`app/services/analysis/`

### 구성 요소

```python
# result_builder.py
class AnalysisResultBuilder:
    """분석 결과 구조화"""

    def build(
        self,
        ai_result: AIAnalysisResult,
        raw_content: RawContent,
        processed_media: ProcessedMedia
    ) -> EnrichedAnalysisResult:
        """
        AI 결과 + 원본 메타데이터 결합

        - AI가 추출한 장소 정보
        - 원본 소스 정보 (URL, 플랫폼 등)
        - 처리 통계 (이미지 수, 처리 시간 등)
        """

        return EnrichedAnalysisResult(
            # AI 분석 결과
            place_info=ai_result.place_info,
            confidence=self._calculate_confidence(ai_result, processed_media),
            reasoning=ai_result.reasoning,

            # 원본 메타데이터
            source_url=raw_content.source,
            platform=raw_content.metadata.get("platform"),

            # 처리 통계
            processing_stats=ProcessingStats(
                num_images_analyzed=len(processed_media.images),
                num_video_frames=len(processed_media.video_frames),
                total_time=...,
            )
        )

    def _calculate_confidence(
        self,
        ai_result: AIAnalysisResult,
        media: ProcessedMedia
    ) -> float:
        """
        종합 신뢰도 계산

        고려 요소:
        - AI 자체 confidence
        - 이미지 품질 및 개수
        - 텍스트 정보 풍부도
