# TRD: 멀티모달 콘텐츠 분석

## 1. 기술 개요
**목적:** PRD 12-multimodal 요구사항을 충족하기 위한 멀티모달 AI 분석 시스템의 기술적 구현 방안 및 아키텍처 설계

**핵심 기술 스택:**
- **AI/ML:** Google Gemini 2.0 Flash Exp (멀티모달 지원 - 텍스트 + 이미지 동시 분석)
- **이미지 처리:** Pillow (PIL) 라이브러리, httpx (비동기 다운로드)
- **영상 처리:** YouTube Data API v3, youtube-transcript-api, (선택) OpenCV
- **캐시:** Redis (L2) + TTLCache (L1 메모리 캐시)
- **API:** FastAPI + Pydantic v2
- **비동기:** asyncio, aiohttp

**기술적 도전 과제:**
1. **이미지 다운로드 최적화:** 고해상도 이미지를 빠르게 다운로드하면서 대역폭 절약
2. **API 비용 관리:** Gemini Vision API는 텍스트만 분석보다 비용 높음 → 캐싱 필수
3. **처리 시간 단축:** 이미지 3장 분석 시 15초 추가 목표 달성
4. **Fallback 처리:** 이미지 다운로드 실패 시에도 서비스 지속

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처 (멀티모달 파이프라인)

```
[Mobile App / Web]
    ↓ POST /api/v1/links/analyze
[API Gateway]
    ↓
[Link Analysis Endpoint]
    ↓
┌─────────────────────────────────────────────────────────┐
│  멀티모달 분석 파이프라인                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Cache Check (Redis L2 + Memory L1)                  │
│     - 캐시 키: hotly:link_analysis:{url_hash}            │
│     - 적중 시: 즉시 반환 (< 1초)                          │
│     ↓ 미적중 시                                          │
│                                                          │
│  2. Content Extraction (ContentExtractor)                │
│     - 플랫폼 감지 (Instagram, YouTube, Naver)            │
│     - 메타데이터 추출 (Open Graph, oEmbed)               │
│     - 이미지 URL 수집 (최대 10장)                         │
│     - 텍스트 추출 (제목, 설명, 해시태그)                   │
│     ↓                                                    │
│                                                          │
│  3. Media Processing (NEW: 이 TRD의 핵심)                │
│     ┌─────────────────────────────────────┐             │
│     │ ImageProcessor                      │             │
│     │ - 이미지 다운로드 (httpx async)       │             │
│     │ - 리사이징 (1024x1024 max)          │             │
│     │ - EXIF 메타데이터 추출               │             │
│     │ - 이미지 품질 검증                   │             │
│     │ - 출력: List[PIL.Image]             │             │
│     └─────────────────────────────────────┘             │
│     ┌─────────────────────────────────────┐             │
│     │ VideoProcessor                      │             │
│     │ - YouTube 썸네일 추출                │             │
│     │ - 프레임 샘플링 (3-5개)             │             │
│     │ - 자막 추출 (youtube-transcript-api) │             │
│     │ - 출력: List[PIL.Image]             │             │
│     └─────────────────────────────────────┘             │
│     ┌─────────────────────────────────────┐             │
│     │ TextProcessor                       │             │
│     │ - 해시태그 추출                      │             │
│     │ - 특수문자 정제                      │             │
│     │ - 키워드 추출                        │             │
│     │ - 출력: CleanedText                 │             │
│     └─────────────────────────────────────┘             │
│     ↓                                                    │
│                                                          │
│  4. AI Analysis (GeminiAnalyzer - 개선)                  │
│     - 입력: 텍스트 + List[PIL.Image]                     │
│     - Gemini 2.0 Flash Exp 호출                          │
│     - 멀티모달 프롬프트 구성                              │
│     - JSON 응답 파싱 및 검증                             │
│     - 출력: PlaceInfo + confidence                       │
│     ↓                                                    │
│                                                          │
│  5. Result Building & Caching                            │
│     - 신뢰도 계산 (텍스트+이미지 종합)                     │
│     - 결과 구조화 (AnalysisResult)                       │
│     - Redis 캐싱 (TTL: 고신뢰도 30일, 저신뢰도 7일)       │
│                                                          │
└─────────────────────────────────────────────────────────┘
    ↓
[Response to Client]
```

### 2-2. 모듈 구조 (새로 추가되는 모듈)

```
backend/app/services/
├── ai/
│   ├── gemini_analyzer.py          # [기존] Gemini API 클라이언트
│   ├── gemini_analyzer_v2.py       # [개선] 멀티모달 최적화 버전
│   └── prompts/
│       ├── multimodal_prompt.py    # [NEW] 멀티모달 프롬프트 템플릿
│       └── prompt_optimizer.py     # [NEW] 프롬프트 최적화 로직
├── media/                          # [NEW] 미디어 처리 모듈
│   ├── __init__.py
│   ├── image_processor.py          # [NEW] 이미지 다운로드/전처리
│   ├── video_processor.py          # [NEW] 영상 프레임 추출
│   ├── text_processor.py           # [NEW] 텍스트 정제
│   └── media_cache.py              # [NEW] 미디어 전용 캐시
├── places/
│   ├── content_extractor.py        # [기존] 콘텐츠 추출
│   ├── place_analysis_service.py   # [개선] 멀티모달 통합
│   └── multimodal_orchestrator.py  # [NEW] 멀티모달 오케스트레이터
└── monitoring/
    └── cache_manager.py            # [기존] 캐시 관리
```

---

## 3. 데이터 모델 설계

### 3-1. Pydantic 스키마 정의

```python
# app/schemas/media.py (NEW)
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from PIL import Image as PILImage


class ImageMetadata(BaseModel):
    """이미지 메타데이터"""
    url: HttpUrl
    width: int
    height: int
    file_size_bytes: int
    format: str  # JPEG, PNG, WebP
    exif_gps: Optional[Dict[str, float]] = None  # {lat: 37.xx, lng: 127.xx}
    exif_datetime: Optional[datetime] = None
    quality_score: float = Field(ge=0.0, le=1.0)  # 0.0~1.0


class ProcessedImage(BaseModel):
    """처리된 이미지 정보"""
    original_url: HttpUrl
    metadata: ImageMetadata
    # PIL.Image는 Pydantic에서 직접 저장 불가 → 메모리에서만 사용
    # image_object는 런타임에서만 유지
    processing_time: float


class VideoFrameMetadata(BaseModel):
    """동영상 프레임 메타데이터"""
    video_url: HttpUrl
    frame_index: int  # 0, 1, 2, ...
    timestamp_seconds: float  # 프레임 추출 위치 (초)
    width: int
    height: int
    quality_score: float


class ProcessedMedia(BaseModel):
    """미디어 처리 결과 (전체)"""

    # 텍스트 정보
    cleaned_text: str
    hashtags: List[str]
    keywords: List[str]

    # 이미지 정보
    images: List[ProcessedImage]
    total_images: int

    # 영상 정보
    video_frames: List[VideoFrameMetadata]
    video_transcript: Optional[str] = None  # YouTube 자막

    # 통계
    processing_time: float
    total_media_size_mb: float

    # 품질 지표
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    confidence_boost: float = Field(ge=0.0, le=1.0)  # 멀티모달로 인한 신뢰도 증가


# app/schemas/ai.py (기존 개선)
class PlaceAnalysisRequest(BaseModel):
    """AI 분석 요청 (멀티모달 지원)"""

    # 텍스트 입력
    content_text: str = Field(..., min_length=1, max_length=10000)
    content_description: Optional[str] = Field(None, max_length=50000)
    hashtags: List[str] = Field(default_factory=list, max_items=50)
    platform: str = Field(..., examples=["instagram", "youtube", "naver_blog"])

    # 이미지 입력 (URL 또는 PIL.Image 객체)
    # API 레벨에서는 URL, 내부 처리에서는 PIL.Image 사용
    images: List[str] = Field(default_factory=list, max_items=10)

    # 멀티모달 관련 플래그
    enable_image_analysis: bool = True  # 이미지 분석 활성화
    max_images_to_analyze: int = Field(default=3, ge=1, le=5)  # 비용 제어

    # 분석 옵션
    include_reasoning: bool = False  # AI 추론 과정 포함 여부
    language: str = Field(default="ko", examples=["ko", "en"])


class MultimodalAnalysisMetadata(BaseModel):
    """멀티모달 분석 메타데이터"""

    # 입력 정보
    num_images_provided: int
    num_images_analyzed: int
    num_video_frames: int
    text_length_chars: int

    # 처리 시간 분해
    image_download_time: float
    image_processing_time: float
    ai_inference_time: float
    total_time: float

    # 품질 지표
    avg_image_quality: float
    text_quality_score: float

    # 분석 근거
    confidence_factors: Dict[str, float]  # {"image_clarity": 0.9, "text_match": 0.8}
    reasoning: Optional[str] = None  # AI가 설명한 추론 과정


class PlaceAnalysisResponse(BaseModel):
    """AI 분석 응답 (멀티모달 정보 포함)"""

    success: bool
    place_info: Optional['PlaceInfo'] = None
    confidence: float = Field(ge=0.0, le=1.0)

    # 멀티모달 관련 추가 정보
    multimodal_metadata: Optional[MultimodalAnalysisMetadata] = None

    # 기존 정보
    analysis_time: float
    error: Optional[str] = None
    model_version: str = "gemini-2.0-flash-exp"
```

### 3-2. 데이터베이스 스키마 (확장)

```sql
-- 기존 analyses 테이블 확장
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS multimodal_metadata JSONB DEFAULT NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS num_images_analyzed INT DEFAULT 0;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS num_video_frames INT DEFAULT 0;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS image_quality_avg DECIMAL(3,2) DEFAULT 0.0;

-- multimodal_metadata JSONB 구조 예시
/*
{
  "images_analyzed": 3,
  "video_frames": 2,
  "image_download_time": 2.5,
  "ai_inference_time": 8.3,
  "confidence_factors": {
    "signboard_detected": 0.95,
    "text_image_match": 0.85,
    "image_quality": 0.90
  },
  "reasoning": "간판에서 '카페 오아시스'를 명확히 인식했고, 해시태그 #성수동과 일치"
}
*/

-- 인덱스 추가
CREATE INDEX idx_analyses_multimodal ON analyses(num_images_analyzed)
  WHERE num_images_analyzed > 0;

CREATE INDEX idx_analyses_confidence ON analyses(confidence DESC)
  WHERE status = 'completed';
```

### 3-3. Redis 캐시 키 구조 (확장)

```python
# app/services/monitoring/cache_manager.py에 추가

class CacheKey:
    """캐시 키 생성 헬퍼 (확장)"""

    @staticmethod
    def link_analysis(url: str) -> str:
        """링크 분석 결과 캐시 (기존)"""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"hotly:link_analysis:{url_hash}"

    @staticmethod
    def multimodal_analysis(url: str, image_hashes: List[str]) -> str:
        """멀티모달 분석 결과 캐시 (NEW)"""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        # 이미지 해시 포함 (이미지가 변경되면 캐시 무효화)
        img_hash = hashlib.sha256("".join(sorted(image_hashes)).encode()).hexdigest()[:8]
        return f"hotly:multimodal:{url_hash}:{img_hash}"

    @staticmethod
    def image_cache(image_url: str) -> str:
        """다운로드된 이미지 메타데이터 캐시 (NEW)"""
        img_hash = hashlib.sha256(image_url.encode()).hexdigest()[:16]
        return f"hotly:image_meta:{img_hash}"

    @staticmethod
    def video_frames(video_id: str) -> str:
        """동영상 프레임 캐시 (NEW)"""
        return f"hotly:video_frames:{video_id}"


# 캐시 TTL 전략 (개선)
class CacheTTL:
    """캐시 만료 시간 상수"""

    # 텍스트만 분석 (기존)
    TEXT_ONLY_LOW_CONFIDENCE = 3600  # 1시간
    TEXT_ONLY_HIGH_CONFIDENCE = 86400 * 7  # 7일

    # 멀티모달 분석 (NEW)
    MULTIMODAL_LOW_CONFIDENCE = 86400 * 7  # 7일 (이미지 있어서 더 안정적)
    MULTIMODAL_HIGH_CONFIDENCE = 86400 * 30  # 30일

    # 미디어 캐시 (NEW)
    IMAGE_METADATA = 86400 * 7  # 7일
    VIDEO_FRAMES = 86400 * 14  # 14일 (변경 빈도 낮음)

    # 다운로드된 이미지 바이너리 (메모리 캐시만, Redis X)
    IMAGE_BINARY_MEMORY = 3600  # 1시간 (메모리 압박 방지)
```

---

## 4. 핵심 모듈 구현

### 4-1. ImageProcessor (이미지 처리 모듈)

```python
# app/services/media/image_processor.py (NEW)
import asyncio
import hashlib
import io
from typing import List, Optional, Tuple
from datetime import datetime

import httpx
from PIL import Image, ExifTags
from pydantic import HttpUrl

from app.core.config import settings
from app.exceptions.media import (
    ImageDownloadError,
    ImageProcessingError,
    InvalidImageError
)
from app.schemas.media import ImageMetadata, ProcessedImage


class ImageProcessor:
    """이미지 다운로드 및 전처리 프로세서"""

    # 설정 상수
    MAX_IMAGE_SIZE_MB = 10
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
    TARGET_MAX_DIMENSION = 1024  # Gemini API 권장 크기
    DOWNLOAD_TIMEOUT = 10  # 초
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF'}

    def __init__(self):
        """이미지 프로세서 초기화"""
        self.http_client = None
        self._download_semaphore = asyncio.Semaphore(3)  # 동시 다운로드 3개 제한

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.DOWNLOAD_TIMEOUT),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.http_client:
            await self.http_client.aclose()

    async def download_and_process_images(
        self,
        image_urls: List[str],
        max_images: int = 3
    ) -> Tuple[List[Image.Image], List[ProcessedImage]]:
        """
        여러 이미지를 다운로드하고 처리

        Args:
            image_urls: 이미지 URL 리스트
            max_images: 처리할 최대 이미지 개수

        Returns:
            (PIL.Image 객체 리스트, ProcessedImage 메타데이터 리스트)
        """
        if not image_urls:
            return [], []

        # 최대 개수 제한
        urls_to_process = image_urls[:max_images]

        # 병렬 다운로드 및 처리
        tasks = [
            self._download_and_process_single(url)
            for url in urls_to_process
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 성공한 결과만 필터링
        pil_images = []
        processed_images = []

        for result in results:
            if isinstance(result, Exception):
                # 개별 이미지 실패는 로깅만 하고 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Image processing failed: {result}")
                continue

            if result:
                pil_image, processed_image = result
                pil_images.append(pil_image)
                processed_images.append(processed_image)

        return pil_images, processed_images

    async def _download_and_process_single(
        self,
        image_url: str
    ) -> Optional[Tuple[Image.Image, ProcessedImage]]:
        """
        단일 이미지 다운로드 및 처리

        Returns:
            (PIL.Image, ProcessedImage) 또는 None (실패 시)
        """
        start_time = asyncio.get_event_loop().time()

        async with self._download_semaphore:  # 동시 다운로드 제한
            try:
                # 1. 이미지 다운로드
                image_bytes = await self._download_image(image_url)

                # 2. PIL.Image로 변환
                pil_image = Image.open(io.BytesIO(image_bytes))

                # 3. 이미지 검증
                await self._validate_image(pil_image)

                # 4. 메타데이터 추출
                metadata = await self._extract_metadata(image_url, pil_image, image_bytes)

                # 5. 리사이징 (필요 시)
                pil_image = await self._resize_if_needed(pil_image)

                # 6. 포맷 정규화 (WebP → JPEG 등)
                pil_image = await self._normalize_format(pil_image)

                processing_time = asyncio.get_event_loop().time() - start_time

                processed_image = ProcessedImage(
                    original_url=image_url,
                    metadata=metadata,
                    processing_time=processing_time
                )

                return pil_image, processed_image

            except Exception as e:
                raise ImageProcessingError(
                    f"Failed to process image {image_url}: {str(e)}"
                )

    async def _download_image(self, url: str) -> bytes:
        """이미지 다운로드"""
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()

            # 크기 검증
            content_length = int(response.headers.get('content-length', 0))
            if content_length > self.MAX_IMAGE_SIZE_BYTES:
                raise ImageDownloadError(
                    f"Image too large: {content_length} bytes (max: {self.MAX_IMAGE_SIZE_BYTES})"
                )

            image_bytes = response.content

            # 실제 크기 검증
            if len(image_bytes) > self.MAX_IMAGE_SIZE_BYTES:
                raise ImageDownloadError(
                    f"Downloaded image too large: {len(image_bytes)} bytes"
                )

            return image_bytes

        except httpx.HTTPStatusError as e:
            raise ImageDownloadError(f"HTTP error {e.response.status_code}: {url}")
        except httpx.TimeoutException:
            raise ImageDownloadError(f"Download timeout: {url}")
        except Exception as e:
            raise ImageDownloadError(f"Download failed: {str(e)}")

    async def _validate_image(self, image: Image.Image) -> None:
        """이미지 유효성 검증"""
        # 포맷 검증
        if image.format not in self.SUPPORTED_FORMATS:
            raise InvalidImageError(
                f"Unsupported format: {image.format}. Supported: {self.SUPPORTED_FORMATS}"
            )

        # 크기 검증
        width, height = image.size
        if width < 100 or height < 100:
            raise InvalidImageError(
                f"Image too small: {width}x{height} (min: 100x100)"
            )

        if width > 10000 or height > 10000:
            raise InvalidImageError(
                f"Image too large: {width}x{height} (max: 10000x10000)"
            )

        # 모드 검증 (손상된 이미지 감지)
        if image.mode not in ('RGB', 'RGBA', 'L', 'P'):
            raise InvalidImageError(f"Invalid image mode: {image.mode}")

    async def _extract_metadata(
        self,
        url: str,
        image: Image.Image,
        image_bytes: bytes
    ) -> ImageMetadata:
        """이미지 메타데이터 추출"""
        width, height = image.size
        file_size = len(image_bytes)

        # EXIF 데이터 추출
        exif_gps = None
        exif_datetime = None

        try:
            exif_data = image._getexif()
            if exif_data:
                # GPS 정보 추출
                gps_info = exif_data.get(34853)  # GPSInfo tag
                if gps_info:
                    exif_gps = self._parse_gps_info(gps_info)

                # 촬영 시간 추출
                datetime_original = exif_data.get(36867)  # DateTimeOriginal
                if datetime_original:
                    try:
                        exif_datetime = datetime.strptime(
                            datetime_original, '%Y:%m:%d %H:%M:%S'
                        )
                    except:
                        pass
        except:
            pass  # EXIF 추출 실패는 무시

        # 이미지 품질 점수 계산
        quality_score = self._calculate_quality_score(image, file_size)

        return ImageMetadata(
            url=url,
            width=width,
            height=height,
            file_size_bytes=file_size,
            format=image.format or 'UNKNOWN',
            exif_gps=exif_gps,
            exif_datetime=exif_datetime,
            quality_score=quality_score
        )

    def _parse_gps_info(self, gps_info: dict) -> Optional[dict]:
        """GPS 정보 파싱"""
        try:
            # GPS 좌표 추출 로직 (복잡하므로 간략화)
            # 실제 구현에서는 GPSInfo 태그를 정확히 파싱 필요
            if not gps_info:
                return None

            # TODO: 실제 GPS 파싱 구현
            return None
        except:
            return None

    def _calculate_quality_score(self, image: Image.Image, file_size: int) -> float:
        """이미지 품질 점수 계산"""
        width, height = image.size
        pixels = width * height

        # 해상도 점수 (0.0 ~ 0.4)
        resolution_score = min(pixels / (1920 * 1080), 1.0) * 0.4

        # 파일 크기 대비 해상도 (압축률 판단) (0.0 ~ 0.3)
        bytes_per_pixel = file_size / pixels if pixels > 0 else 0
        # 적정 압축: 0.5~3.0 bytes/pixel
        compression_score = 0.3 if 0.5 <= bytes_per_pixel <= 3.0 else 0.15

        # 종횡비 정상성 (0.0 ~ 0.3)
        aspect_ratio = width / height if height > 0 else 0
        # 정상 범위: 0.5 ~ 2.0
        aspect_score = 0.3 if 0.5 <= aspect_ratio <= 2.0 else 0.1

        return min(resolution_score + compression_score + aspect_score, 1.0)

    async def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """필요 시 이미지 리사이징"""
        width, height = image.size
        max_dim = max(width, height)

        if max_dim <= self.TARGET_MAX_DIMENSION:
            return image  # 리사이징 불필요

        # 종횡비 유지하면서 리사이징
        scale = self.TARGET_MAX_DIMENSION / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized

    async def _normalize_format(self, image: Image.Image) -> Image.Image:
        """이미지 포맷 정규화"""
        # RGBA를 RGB로 변환 (Gemini는 RGB 선호)
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # alpha 채널 사용
            return rgb_image

        # 팔레트 모드를 RGB로 변환
        if image.mode == 'P':
            return image.convert('RGB')

        # 그레이스케일을 RGB로 변환 (선택적)
        if image.mode == 'L':
            return image.convert('RGB')

        return image
```

### 4-2. VideoProcessor (영상 처리 모듈)

```python
# app/services/media/video_processor.py (NEW)
import asyncio
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

import httpx
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from app.core.config import settings
from app.exceptions.media import VideoProcessingError
from app.schemas.media import VideoFrameMetadata


class VideoProcessor:
    """동영상 프레임 추출 및 처리"""

    # YouTube 썸네일 URL 패턴
    YOUTUBE_THUMBNAIL_URLS = [
        "https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",  # 1280x720
        "https://img.youtube.com/vi/{video_id}/sddefault.jpg",      # 640x480
        "https://img.youtube.com/vi/{video_id}/hqdefault.jpg",      # 480x360
    ]

    def __init__(self):
        """동영상 프로세서 초기화"""
        self.http_client = None

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=10.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    async def process_video(
        self,
        video_url: str
    ) -> Tuple[List[Image.Image], List[VideoFrameMetadata], Optional[str]]:
        """
        동영상 처리 (썸네일 + 자막)

        Returns:
            (프레임 이미지 리스트, 프레임 메타데이터 리스트, 자막 텍스트)
        """
        # 플랫폼 감지
        platform = self._detect_platform(video_url)

        if platform == 'youtube':
            return await self._process_youtube_video(video_url)
        else:
            # 다른 플랫폼은 향후 구현
            raise VideoProcessingError(f"Unsupported video platform: {platform}")

    def _detect_platform(self, url: str) -> str:
        """동영상 플랫폼 감지"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        return 'unknown'

    async def _process_youtube_video(
        self,
        youtube_url: str
    ) -> Tuple[List[Image.Image], List[VideoFrameMetadata], Optional[str]]:
        """YouTube 영상 처리"""
        # 1. Video ID 추출
        video_id = self._extract_youtube_video_id(youtube_url)
        if not video_id:
            raise VideoProcessingError("Invalid YouTube URL")

        # 2. 썸네일 다운로드 (병렬)
        thumbnail_task = self._download_youtube_thumbnail(video_id, youtube_url)

        # 3. 자막 추출 (병렬)
        transcript_task = self._extract_youtube_transcript(video_id)

        # 병렬 실행
        results = await asyncio.gather(
            thumbnail_task,
            transcript_task,
            return_exceptions=True
        )

        thumbnail_result = results[0]
        transcript_result = results[1]

        # 썸네일 처리
        frames = []
        frame_metadata = []

        if not isinstance(thumbnail_result, Exception) and thumbnail_result:
            frame_img, frame_meta = thumbnail_result
            frames.append(frame_img)
            frame_metadata.append(frame_meta)

        # 자막 처리
        transcript = None
        if not isinstance(transcript_result, Exception):
            transcript = transcript_result

        return frames, frame_metadata, transcript

    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """YouTube Video ID 추출"""
        # youtu.be/VIDEO_ID
        match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        # youtube.com/watch?v=VIDEO_ID
        match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        # youtube.com/embed/VIDEO_ID
        match = re.search(r'/embed/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        return None

    async def _download_youtube_thumbnail(
        self,
        video_id: str,
        video_url: str
    ) -> Optional[Tuple[Image.Image, VideoFrameMetadata]]:
        """YouTube 썸네일 다운로드 (여러 해상도 시도)"""
        for thumbnail_url_template in self.YOUTUBE_THUMBNAIL_URLS:
            thumbnail_url = thumbnail_url_template.format(video_id=video_id)

            try:
                response = await self.http_client.get(thumbnail_url)
                if response.status_code == 200:
                    # 이미지 변환
                    from io import BytesIO
                    image = Image.open(BytesIO(response.content))

                    # 메타데이터 생성
                    width, height = image.size
                    metadata = VideoFrameMetadata(
                        video_url=video_url,
                        frame_index=0,  # 썸네일은 0번
                        timestamp_seconds=0.0,
                        width=width,
                        height=height,
                        quality_score=0.8  # 썸네일 품질은 일반적으로 양호
                    )

                    return image, metadata
            except:
                continue  # 다음 해상도 시도

        return None

    async def _extract_youtube_transcript(
        self,
        video_id: str
    ) -> Optional[str]:
        """YouTube 자막 추출"""
        try:
            # 언어 우선순위: 한국어 > 영어
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 자동 생성 자막 포함하여 찾기
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['ko', 'en'])
            except NoTranscriptFound:
                # 수동 자막 없으면 자동 생성 자막
                try:
                    transcript = transcript_list.find_generated_transcript(['ko', 'en'])
                except:
                    return None

            if transcript:
                # 자막 데이터 가져오기
                transcript_data = transcript.fetch()

                # 텍스트만 추출하여 결합
                text_parts = [entry['text'] for entry in transcript_data]
                full_text = ' '.join(text_parts)

                # 길이 제한 (Gemini API 제한 고려)
                if len(full_text) > 10000:
                    full_text = full_text[:10000] + "..."

                return full_text

        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to extract YouTube transcript: {e}")
            return None
```

### 4-3. GeminiAnalyzer 개선 (멀티모달 최적화)

```python
# app/services/ai/gemini_analyzer_v2.py (NEW - 멀티모달 최적화 버전)
import asyncio
import json
import time
from typing import List, Dict, Any, Optional

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.exceptions.ai import (
    AIAnalysisError,
    RateLimitError,
    InvalidResponseError,
    AIServiceUnavailableError
)
from app.schemas.ai import PlaceAnalysisRequest, PlaceInfo, MultimodalAnalysisMetadata
from app.services.ai.prompts.multimodal_prompt import MULTIMODAL_PLACE_EXTRACTION_PROMPT


class GeminiAnalyzerV2:
    """
    Gemini 2.0 Flash Exp 기반 멀티모달 분석기 (개선 버전)

    개선 사항:
    - PIL.Image 객체 직접 처리
    - 멀티모달 프롬프트 최적화
    - 이미지 분석 결과를 confidence에 반영
    - 상세한 메타데이터 수집
    """

    def __init__(self) -> None:
        """Gemini 분석기 초기화"""
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model_name = "gemini-2.0-flash-exp"
        self.timeout = 60
        self.max_retries = 3
        self.base_delay = 1.0

    async def analyze_multimodal_content(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]] = None
    ) -> Tuple[PlaceInfo, MultimodalAnalysisMetadata]:
        """
        멀티모달 콘텐츠 분석 (텍스트 + 이미지)

        Args:
            request: 분석 요청 (텍스트 정보 포함)
            pil_images: PIL.Image 객체 리스트

        Returns:
            (PlaceInfo, MultimodalAnalysisMetadata)
        """
        start_time = time.time()

        try:
            # 메타데이터 초기화
            metadata = MultimodalAnalysisMetadata(
                num_images_provided=len(request.images),
                num_images_analyzed=len(pil_images) if pil_images else 0,
                num_video_frames=0,  # TODO: 영상 프레임 지원 시 업데이트
                text_length_chars=len(request.content_text or ""),
                image_download_time=0.0,
                image_processing_time=0.0,
                ai_inference_time=0.0,
                total_time=0.0,
                avg_image_quality=0.0,
                text_quality_score=self._calculate_text_quality(request),
                confidence_factors={}
            )

            # 프롬프트 생성
            prompt = self._format_multimodal_prompt(request, pil_images)

            # Gemini API 호출
            ai_start_time = time.time()
            response_text = await self._call_gemini_api_with_retry(prompt, pil_images)
            metadata.ai_inference_time = time.time() - ai_start_time

            # 응답 파싱
            place_data = self._parse_and_validate_response(response_text)

            # PlaceInfo 생성
            place_info = PlaceInfo(**place_data)

            # Confidence factors 계산
            metadata.confidence_factors = self._calculate_confidence_factors(
                request,
                pil_images,
                place_info
            )

            # 추론 과정 추가 (요청 시)
            if request.include_reasoning:
                metadata.reasoning = self._generate_reasoning(
                    request, pil_images, place_info
                )

            # 총 처리 시간
            metadata.total_time = time.time() - start_time

            return place_info, metadata

        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError, InvalidResponseError)):
                raise
            raise AIAnalysisError(f"Multimodal analysis failed: {str(e)}")

    def _format_multimodal_prompt(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]]
    ) -> str:
        """멀티모달 프롬프트 생성"""
        hashtags_str = " ".join(request.hashtags) if request.hashtags else "없음"

        # 이미지 개수에 따른 프롬프트 조정
        image_instruction = ""
        if pil_images and len(pil_images) > 0:
            image_instruction = f"""

## 🖼️ 이미지 분석 지침
{len(pil_images)}장의 이미지가 제공되었습니다. 다음을 중점적으로 분석하세요:
1. **간판/상호명**: 이미지 속 텍스트(간판, 메뉴판 등)를 정확히 읽어 장소명 추출
2. **인테리어/외관**: 카페/레스토랑/관광지 등 카테고리 판단
3. **음식/메뉴**: 제공하는 음식 종류로 카테고리 보강
4. **위치 단서**: 랜드마크, 주변 환경으로 위치 추정
5. **텍스트 일치도**: 이미지 속 정보와 캡션/해시태그 교차 검증

**중요**: 이미지에서 명확히 읽을 수 있는 정보를 최우선으로 사용하세요.
"""

        from app.services.ai.prompts.multimodal_prompt import get_multimodal_prompt
        prompt = get_multimodal_prompt(
            platform=request.platform,
            title=request.content_text or "없음",
            description=request.content_description or "없음",
            hashtags=hashtags_str,
            image_instruction=image_instruction
        )

        return prompt

    async def _call_gemini_api_with_retry(
        self,
        prompt: str,
        images: Optional[List[Image.Image]]
    ) -> str:
        """Gemini API 호출 (재시도 포함)"""
        for attempt in range(self.max_retries):
            try:
                return await self._call_gemini_api(prompt, images)
            except RateLimitError:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            except AIServiceUnavailableError:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        raise AIAnalysisError("Max retries exceeded")

    async def _call_gemini_api(
        self,
        prompt: str,
        images: Optional[List[Image.Image]]
    ) -> str:
        """Gemini API 호출 (멀티모달)"""
        try:
            if not hasattr(settings, "GEMINI_API_KEY") or not settings.GEMINI_API_KEY:
                raise AIServiceUnavailableError("Gemini API key not configured")

            model = genai.GenerativeModel(self.model_name)

            # 콘텐츠 구성
            if images and len(images) > 0:
                # 멀티모달: [prompt, image1, image2, ...]
                content = [prompt] + images
            else:
                # 텍스트만
                content = prompt

            # API 호출
            response = await asyncio.to_thread(
                model.generate_content,
                content,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # 낮은 온도로 일관성 확보
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            if not response or not response.text:
                raise InvalidResponseError("Empty response from Gemini")

            response_text = response.text.strip()

            # Markdown code block 제거
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            return response_text

        except Exception as e:
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Gemini rate limit: {str(e)}")
            if "unavailable" in error_msg or "503" in error_msg or "500" in error_msg:
                raise AIServiceUnavailableError(f"Gemini unavailable: {str(e)}")
            if "api key" in error_msg or "401" in error_msg:
                raise AIServiceUnavailableError(f"Gemini auth failed: {str(e)}")

            if isinstance(e, (RateLimitError, AIServiceUnavailableError, InvalidResponseError)):
                raise

            raise AIAnalysisError(f"Gemini API call failed: {str(e)}")

    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """응답 JSON 파싱 및 검증"""
        try:
            response_data = json.loads(response_text)

            # 기본 필드 검증
            if "name" not in response_data:
                raise InvalidResponseError("Missing 'name' field in response")

            return response_data

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise AIAnalysisError(f"Failed to parse response: {str(e)}")

    def _calculate_text_quality(self, request: PlaceAnalysisRequest) -> float:
        """텍스트 품질 점수 계산"""
        score = 0.0

        # 제목 길이
        if request.content_text and len(request.content_text) > 10:
            score += 0.3

        # 설명 존재
        if request.content_description and len(request.content_description) > 20:
            score += 0.3

        # 해시태그 개수
        if request.hashtags:
            score += min(len(request.hashtags) * 0.1, 0.4)

        return min(score, 1.0)

    def _calculate_confidence_factors(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]],
        place_info: PlaceInfo
    ) -> Dict[str, float]:
        """신뢰도 요소별 점수 계산"""
        factors = {}

        # 텍스트 풍부도
        factors["text_richness"] = self._calculate_text_quality(request)

        # 이미지 제공 여부
        if pil_images and len(pil_images) > 0:
            factors["image_provided"] = 1.0
            factors["image_count_boost"] = min(len(pil_images) * 0.2, 0.6)
        else:
            factors["image_provided"] = 0.0
            factors["image_count_boost"] = 0.0

        # 추출 정보 완성도
        factors["name_extracted"] = 1.0 if place_info.name else 0.0
        factors["address_extracted"] = 0.8 if place_info.address else 0.0
        factors["category_extracted"] = 0.6 if place_info.category else 0.0

        # 종합 신뢰도
        factors["overall_confidence"] = sum(factors.values()) / len(factors)

        return factors

    def _generate_reasoning(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]],
        place_info: PlaceInfo
    ) -> str:
        """AI 추론 과정 생성"""
        reasoning_parts = []

        if pil_images and len(pil_images) > 0:
            reasoning_parts.append(
                f"{len(pil_images)}장의 이미지를 분석하여 간판, 인테리어, 메뉴 정보를 파악했습니다."
            )

        if request.hashtags:
            reasoning_parts.append(
                f"해시태그 {len(request.hashtags)}개를 분석하여 카테고리를 판단했습니다."
            )

        if place_info.name:
            reasoning_parts.append(
                f"장소명 '{place_info.name}'을(를) 추출했습니다."
            )

        return " ".join(reasoning_parts)
```

### 4-4. MultimodalOrchestrator (통합 오케스트레이터)

```python
# app/services/places/multimodal_orchestrator.py (NEW)
import asyncio
import time
from typing import List, Optional, Tuple

from PIL import Image

from app.schemas.ai import PlaceAnalysisRequest, PlaceInfo, MultimodalAnalysisMetadata
from app.schemas.content import ContentMetadata
from app.schemas.media import ProcessedMedia, ProcessedImage
from app.services.ai.gemini_analyzer_v2 import GeminiAnalyzerV2
from app.services.media.image_processor import ImageProcessor
from app.services.media.video_processor import VideoProcessor
from app.services.media.text_processor import TextProcessor
from app.exceptions.media import ImageProcessingError, VideoProcessingError


class MultimodalOrchestrator:
    """
    멀티모달 분석 오케스트레이터

    역할:
    1. 미디어 프로세싱 조율 (이미지, 영상, 텍스트)
    2. AI 분석 호출
    3. 결과 통합 및 신뢰도 계산
    4. Fallback 전략 실행
    """

    def __init__(self):
        """오케스트레이터 초기화"""
        self.ai_analyzer = GeminiAnalyzerV2()
        self.text_processor = TextProcessor()

    async def analyze_content(
        self,
        content_metadata: ContentMetadata,
        enable_image_analysis: bool = True,
        max_images: int = 3
    ) -> Tuple[PlaceInfo, float, MultimodalAnalysisMetadata]:
        """
        콘텐츠 종합 분석 (텍스트 + 이미지 + 영상)

        Args:
            content_metadata: 추출된 콘텐츠 메타데이터
            enable_image_analysis: 이미지 분석 활성화 여부
            max_images: 분석할 최대 이미지 개수

        Returns:
            (PlaceInfo, confidence, MultimodalAnalysisMetadata)
        """
        start_time = time.time()

        # 1. 텍스트 처리
        cleaned_text = await self.text_processor.clean_text(
            content_metadata.title or ""
        )
        hashtags = await self.text_processor.extract_hashtags(
            content_metadata.description or ""
        )

        # 2. 이미지 처리 (선택적)
        pil_images: List[Image.Image] = []
        processed_images: List[ProcessedImage] = []
        image_download_time = 0.0
        image_processing_time = 0.0

        if enable_image_analysis and content_metadata.images:
            try:
                img_start = time.time()
                async with ImageProcessor() as img_processor:
                    pil_images, processed_images = await img_processor.download_and_process_images(
                        content_metadata.images,
                        max_images=max_images
                    )
                image_processing_time = time.time() - img_start

                if pil_images:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Successfully processed {len(pil_images)} images in {image_processing_time:.2f}s"
                    )
            except ImageProcessingError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Image processing failed, falling back to text-only: {e}")
                # Fallback: 텍스트만으로 분석 진행

        # 3. 영상 처리 (선택적, YouTube만 지원)
        video_frames: List[Image.Image] = []
        video_transcript: Optional[str] = None

        # TODO: 영상 URL 감지 및 처리
        # if video_url:
        #     async with VideoProcessor() as video_processor:
        #         frames, metadata, transcript = await video_processor.process_video(video_url)
        #         video_frames.extend(frames)
        #         video_transcript = transcript

        # 4. AI 분석 요청 준비
        ai_request = PlaceAnalysisRequest(
            content_text=cleaned_text,
            content_description=content_metadata.description,
            hashtags=hashtags or [],
            images=[],  # URL은 이미 다운로드 완료
            platform=getattr(content_metadata, 'platform', 'unknown'),
            enable_image_analysis=enable_image_analysis,
            max_images_to_analyze=max_images
        )

        # 5. AI 멀티모달 분석
        all_images = pil_images + video_frames
        place_info, ai_metadata = await self.ai_analyzer.analyze_multimodal_content(
            ai_request,
            pil_images=all_images if all_images else None
        )

        # 6. 메타데이터 보강
        ai_metadata.image_download_time = image_download_time
        ai_metadata.image_processing_time = image_processing_time
        ai_metadata.num_video_frames = len(video_frames)

        # 평균 이미지 품질 계산
        if processed_images:
            avg_quality = sum(img.metadata.quality_score for img in processed_images) / len(processed_images)
            ai_metadata.avg_image_quality = avg_quality
        else:
            ai_metadata.avg_image_quality = 0.0

        # 7. 종합 신뢰도 계산
        final_confidence = self._calculate_final_confidence(
            ai_metadata.confidence_factors,
            len(pil_images),
            len(video_frames),
            ai_metadata.text_quality_score
        )

        # 8. 총 처리 시간
        ai_metadata.total_time = time.time() - start_time

        return place_info, final_confidence, ai_metadata

    def _calculate_final_confidence(
        self,
        confidence_factors: dict,
        num_images: int,
        num_video_frames: int,
        text_quality: float
    ) -> float:
        """
        종합 신뢰도 계산

        고려 요소:
        - AI 자체 confidence
        - 이미지 개수 및 품질
        - 텍스트 품질
        - 정보 완성도
        """
        # 기본 신뢰도 (AI confidence factors 평균)
        base_confidence = confidence_factors.get('overall_confidence', 0.5)

        # 멀티모달 보너스
        multimodal_bonus = 0.0

        if num_images > 0:
            # 이미지 개수에 따른 보너스 (최대 +0.2)
            multimodal_bonus += min(num_images * 0.1, 0.2)

        if num_video_frames > 0:
            # 영상 프레임 보너스 (최대 +0.1)
            multimodal_bonus += min(num_video_frames * 0.05, 0.1)

        # 텍스트 품질 보너스 (최대 +0.1)
        text_bonus = text_quality * 0.1

        # 종합 신뢰도 (최대 1.0)
        final = min(base_confidence + multimodal_bonus + text_bonus, 1.0)

        return final
```

---

## 5. 프롬프트 엔지니어링

### 5-1. 멀티모달 프롬프트 템플릿

```python
# app/services/ai/prompts/multimodal_prompt.py (NEW)

MULTIMODAL_PLACE_EXTRACTION_PROMPT_V1 = """
# 🎯 장소 정보 추출 전문가 AI

당신은 SNS 콘텐츠(텍스트 + 이미지)에서 장소 정보를 정확히 추출하는 AI입니다.

## 📋 입력 정보

**플랫폼:** {platform}
**제목/캡��:** {title}
**설명:** {description}
**해시태그:** {hashtags}

{image_instruction}

## 🎯 추출 목표

다음 정보를 **JSON 형식**으로 추출하세요:

```json
{{
  "name": "장소명 (필수)",
  "address": "상세 주소 (선택)",
  "category": ["카테고리1", "카테고리2"],
  "business_hours": "영업시간 (선택)",
  "phone": "전화번호 (선택)",
  "keywords": ["키워드1", "키워드2"],
  "description": "간단한 설명 (50자 이내)",
  "confidence": 0.95
}}
```

## 📐 추출 규칙

### 1️⃣ 장소명 (name) - 필수
- **우선순위 1**: 이미지 속 간판/상호명에서 OCR로 읽은 텍스트
- **우선순위 2**: 캡션/제목에서 명확히 언급된 장소명
- **우선순위 3**: 해시태그에서 추론한 장소명
- **형식**: 정확한 공식 상호명 (예: "카페 오아시스", "명동 교자")
- **주의**: 추측이 아닌 명확한 증거가 있어야 함

### 2️⃣ 주소 (address) - 선택
- **우선순위 1**: 이미지 속 주소 텍스트 (명함, 안내판 등)
- **우선순위 2**: 캡션/설명에 명시된 주소
- **우선순위 3**: 해시태그로 추론한 지역 (예: #성수동 → "서울 성동구 성수동")
- **형식**: "시/도 구/군 동/읍/면" 형식
- **불확실하면**: null 반환 (잘못된 주소보다 나음)

### 3️⃣ 카테고리 (category) - 필수
**가능한 카테고리:**
- "카페" (커피, 디저트 제공)
- "레스토랑" (식사 제공)
- "한식" / "중식" / "일식" / "양식" / "아시안" (음식 종류)
- "술집" / "바" (주류 제공)
- "베이커리" (빵, 케이크)
- "관광지" (명소, 랜드마크)
- "문화공간" (미술관, 갤러리)
- "호텔" / "숙박"
- "쇼핑" (매장, 마켓)
- "기타"

**판단 근거:**
- 이미지 속 음식/인테리어
- 메뉴판 내용
- 캡션/해시태그 (#카페, #맛집 등)

**예시:**
- 커피 사진 + 디저트 → ["카페", "베이커리"]
- 파스타 사진 + 와인 → ["레스토랑", "양식"]

### 4️⃣ 영업시간 (business_hours) - 선택
- 이미지 속 안내판/명함에서만 추출
- 없으면 null

### 5️⃣ 전화번호 (phone) - 선택
- 이미지 속 텍스트에서만 추출
- 형식: "000-0000-0000" 또는 "02-000-0000"

### 6️⃣ 키워드 (keywords)
- 장소의 특징을 나타내는 단어 3-10개
- 예: ["데이트", "브런치", "루프탑", "감성", "인스타", "핫플"]

### 7️⃣ 설명 (description)
- 장소 특징 요약 (50자 이내)
- 예: "북유럽 감성의 브런치 카페, 루프탑 좌석 인기"

### 8️⃣ 신뢰도 (confidence)
**0.0 ~ 1.0 점수:**
- **0.9-1.0**: 간판 명확 + 주소 확인 + 카테고리 명확
- **0.7-0.9**: 장소명 명확 + 카테고리 명확 (주소 추정)
- **0.5-0.7**: 장소명 추정 + 카테고리 명확
- **0.3-0.5**: 정보 부족, 추측 많음
- **0.0-0.3**: 신뢰할 수 없는 추측

## 🚨 중요 원칙

1. **이미지 우선**: 이미지에서 읽은 정보가 텍스트보다 우선
2. **사실만 추출**: 추측하지 말고, 명확한 증거가 있는 것만 추출
3. **불확실하면 null**: 잘못된 정보보다 누락이 나음
4. **JSON만 반환**: 설명 없이 JSON만 출력

## 📤 출력 형식

**반드시 아래 JSON 스키마를 따르세요:**

{json_schema}

---

이제 위 정보를 바탕으로 장소 정보를 JSON으로 추출하세요.
"""


def get_multimodal_prompt(
    platform: str,
    title: str,
    description: str,
    hashtags: str,
    image_instruction: str = ""
) -> str:
    """멀티모달 프롬프트 생성"""

    # JSON 스키마
    json_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "address": {"type": ["string", "null"]},
            "category": {"type": "array", "items": {"type": "string"}},
            "business_hours": {"type": ["string", "null"]},
            "phone": {"type": ["string", "null"]},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string", "maxLength": 50},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
        },
        "required": ["name", "category", "confidence"]
    }

    import json
    return MULTIMODAL_PLACE_EXTRACTION_PROMPT_V1.format(
        platform=platform,
        title=title,
        description=description,
        hashtags=hashtags,
        image_instruction=image_instruction or "",
        json_schema=json.dumps(json_schema, indent=2, ensure_ascii=False)
    )
```

### 5-2. 프롬프트 최적화 전략

```python
# app/services/ai/prompts/prompt_optimizer.py (NEW)

class PromptOptimizer:
    """프롬프트 최적화 도구"""

    @staticmethod
    def optimize_for_image_count(base_prompt: str, num_images: int) -> str:
        """이미지 개수에 따른 프롬프트 최적화"""

        if num_images == 0:
            # 텍스트만: 간판 언급 제거
            return base_prompt.replace("이미지 속 간판", "텍스트에서 명시된")

        elif num_images == 1:
            # 이미지 1장: 간판 집중
            emphasis = "\n⚠️ 제공된 이미지 1장에서 간판/상호명을 최우선으로 읽어주세요."
            return base_prompt + emphasis

        elif num_images >= 3:
            # 이미지 여러 장: 비교 분석
            emphasis = "\n⚠️ 여러 이미지를 비교하여 일관성 있는 정보를 추출하세요."
            return base_prompt + emphasis

        return base_prompt

    @staticmethod
    def add_few_shot_examples(base_prompt: str, platform: str) -> str:
        """플랫폼별 Few-shot 예제 추가"""

        examples = {
            "instagram": """
## 📝 예시 (Instagram)

**입력:**
- 캡션: "오늘의 힐링 ☕️✨"
- 해시태그: #카페 #성수동 #브런치
- 이미지: [외관 사진 - "CAFE OASIS" 간판 보임]

**출력:**
```json
{
  "name": "CAFE OASIS",
  "address": "서울 성동구 성수동",
  "category": ["카페", "브런치"],
  "keywords": ["힐링", "성수동", "브런치"],
  "description": "성수동의 브런치 카페",
  "confidence": 0.92
}
```
""",
            "youtube": """
## 📝 예시 (YouTube)

**입력:**
- 제목: "성수동 맛집 VLOG"
- 이미지: [썸네일 - 음식 사진]
- 자막: "오늘은 성수동 새로 생긴 파스타 맛집에 왔어요"

**출력:**
```json
{
  "name": "성수동 파스타 맛집",
  "address": "서울 성동구 성수동",
  "category": ["레스토랑", "양식"],
  "keywords": ["맛집", "파스타", "성수동"],
  "description": "성수동 파스타 전문 레스토랑",
  "confidence": 0.75
}
```
"""
        }

        example = examples.get(platform, "")
        return base_prompt + example
```

---

## 6. 캐싱 전략 (멀티모달 특화)

### 6-1. 미디어 전용 캐시 레이어

```python
# app/services/media/media_cache.py (NEW)
import asyncio
from typing import Optional, Dict
from datetime import timedelta
from cachetools import TTLCache
from PIL import Image
import io

from app.services.monitoring.cache_manager import CacheManager, CacheKey, CacheTTL


class MediaCacheManager:
    """
    미디어 전용 캐시 관리자

    레이어:
    - L1: 메모리 (PIL.Image 바이너리, TTL 1시간)
    - L2: Redis (이미지 메타데이터만, TTL 7일)
    """

    def __init__(self):
        """미디어 캐시 초기화"""
        # L1: 메모리 캐시 (이미지 바이너리)
        self.image_memory_cache: TTLCache = TTLCache(
            maxsize=100,  # 최대 100장
            ttl=CacheTTL.IMAGE_BINARY_MEMORY
        )

        # L2: Redis (메타데이터만)
        self.redis_cache = CacheManager()

    async def get_image(self, image_url: str) -> Optional[Image.Image]:
        """
        캐시에서 이미지 가져오기

        Returns:
            PIL.Image 또는 None (캐시 미스)
        """
        cache_key = self._get_image_key(image_url)

        # L1 캐시 확인 (메모리)
        if cache_key in self.image_memory_cache:
            image_bytes = self.image_memory_cache[cache_key]
            return Image.open(io.BytesIO(image_bytes))

        # L2 캐시 확인 (Redis - 메타데이터만, 바이너리는 너무 큼)
        # Redis에는 메타데이터만 저장 (다운로드 성공 여부)
        # 실제 이미지는 재다운로드 필요

        return None

    async def cache_image(
        self,
        image_url: str,
        pil_image: Image.Image,
        metadata: dict
    ) -> None:
        """
        이미지를 캐시에 저장

        Args:
            image_url: 원본 URL
            pil_image: PIL.Image 객체
            metadata: 이미지 메타데이터
        """
        cache_key = self._get_image_key(image_url)

        # L1: 메모리에 바이너리 저장 (압축)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        image_bytes = buffer.getvalue()

        # 크기 제한 (5MB 이하만 캐싱)
        if len(image_bytes) < 5 * 1024 * 1024:
            self.image_memory_cache[cache_key] = image_bytes

        # L2: Redis에 메타데이터만 저장
        await self.redis_cache.initialize()
        redis_key = CacheKey.image_cache(image_url)
        await self.redis_cache.set(
            redis_key,
            metadata,
            ttl=CacheTTL.IMAGE_METADATA
        )
        await self.redis_cache.close()

    def _get_image_key(self, url: str) -> str:
        """이미지 캐시 키 생성"""
        import hashlib
        return hashlib.sha256(url.encode()).hexdigest()[:16]
```

### 6-2. 캐시 무효화 전략

```python
# app/services/media/cache_invalidation.py (NEW)
from typing import List
from app.services.monitoring.cache_manager import CacheManager, CacheKey


class MediaCacheInvalidator:
    """미디어 캐시 무효화 관리"""

    def __init__(self):
        self.cache_manager = CacheManager()

    async def invalidate_link_analysis(self, url: str) -> None:
        """링크 분석 결과 캐시 무효화"""
        await self.cache_manager.initialize()

        cache_key = CacheKey.link_analysis(url)
        await self.cache_manager.invalidate(cache_key)

        await self.cache_manager.close()

    async def invalidate_images(self, image_urls: List[str]) -> None:
        """이미지 캐시 일괄 무효화"""
        await self.cache_manager.initialize()

        for url in image_urls:
            cache_key = CacheKey.image_cache(url)
            await self.cache_manager.invalidate(cache_key)

        await self.cache_manager.close()

    async def invalidate_multimodal_analysis(
        self,
        url: str,
        image_hashes: List[str]
    ) -> None:
        """멀티모달 분석 결과 캐시 무효화"""
        await self.cache_manager.initialize()

        cache_key = CacheKey.multimodal_analysis(url, image_hashes)
        await self.cache_manager.invalidate(cache_key)

        await self.cache_manager.close()
```

---

## 7. 에러 처리 및 Fallback 전략

### 7-1. 예외 계층 구조

```python
# app/exceptions/media.py (NEW)

class MediaError(Exception):
    """미디어 처리 기본 예외"""
    pass


class ImageDownloadError(MediaError):
    """이미지 다운로드 실패"""
    pass


class ImageProcessingError(MediaError):
    """이미지 처리 실패"""
    pass


class InvalidImageError(MediaError):
    """유효하지 않은 이미지"""
    pass


class VideoProcessingError(MediaError):
    """동영상 처리 실패"""
    pass


class MediaTimeoutError(MediaError):
    """미디어 처리 타임아웃"""
    pass
```

### 7-2. Fallback 전략 구현

```python
# app/services/places/fallback_strategy.py (NEW)
import logging
from typing import Optional, Tuple

from app.schemas.ai import PlaceInfo, MultimodalAnalysisMetadata
from app.schemas.content import ContentMetadata
from app.services.places.place_analysis_service import PlaceAnalysisService
from app.exceptions.media import ImageProcessingError, VideoProcessingError

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """멀티모달 분석 실패 시 Fallback 전략"""

    def __init__(self):
        self.text_only_service = PlaceAnalysisService()

    async def handle_image_failure(
        self,
        content_metadata: ContentMetadata,
        error: Exception
    ) -> Tuple[PlaceInfo, float, Optional[MultimodalAnalysisMetadata]]:
        """
        이미지 처리 실패 시 Fallback

        전략: 텍스트만으로 분석
        """
        logger.warning(f"Image processing failed, falling back to text-only: {error}")

        # 텍스트 기반 분석
        result = await self.text_only_service.analyze_content(
            content_metadata,
            images=[]  # 이미지 없이
        )

        if not result.success:
            raise Exception("Text-only fallback also failed")

        # 메타데이터 생성
        metadata = MultimodalAnalysisMetadata(
            num_images_provided=len(content_metadata.images or []),
            num_images_analyzed=0,  # 이미지 분석 실패
            num_video_frames=0,
            text_length_chars=len(content_metadata.title or ""),
            image_download_time=0.0,
            image_processing_time=0.0,
            ai_inference_time=result.analysis_time,
            total_time=result.analysis_time,
            avg_image_quality=0.0,
            text_quality_score=0.5,
            confidence_factors={
                "fallback_mode": 1.0,
                "text_only": 1.0
            },
            reasoning="이미지 처리 실패로 텍스트 기반 분석으로 전환"
        )

        return result.place_info, result.confidence, metadata

    async def handle_partial_image_failure(
        self,
        successful_images: int,
        failed_images: int,
        place_info: PlaceInfo,
        confidence: float,
        metadata: MultimodalAnalysisMetadata
    ) -> Tuple[PlaceInfo, float, MultimodalAnalysisMetadata]:
        """
        일부 이미지만 처리 성공 시

        전략: 성공한 이미지로 분석 계속, 신뢰도 조정
        """
        logger.warning(
            f"Partial image processing: {successful_images} succeeded, {failed_images} failed"
        )

        # 신뢰도 페널티 적용
        penalty = min(failed_images * 0.1, 0.3)  # 최대 -0.3
        adjusted_confidence = max(confidence - penalty, 0.0)

        # 메타데이터 업데이트
        metadata.confidence_factors["partial_failure_penalty"] = penalty
        metadata.reasoning = (
            f"{metadata.reasoning} (일부 이미지 처리 실패: {failed_images}장)"
        )

        return place_info, adjusted_confidence, metadata
```

---

## 8. 성능 최적화

### 8-1. 병렬 처리 최적화

```python
# app/services/media/parallel_processor.py (NEW)
import asyncio
from typing import List, TypeVar, Callable, Any
from concurrent.futures import ThreadPoolExecutor

T = TypeVar('T')


class ParallelMediaProcessor:
    """미디어 병렬 처리 최적화"""

    def __init__(self, max_workers: int = 3):
        """
        Args:
            max_workers: 최대 동시 작업 수 (이미지 다운로드 3개 권장)
        """
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_batch(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        fail_fast: bool = False
    ) -> List[Any]:
        """
        여러 아이템을 병렬 처리

        Args:
            items: 처리할 아이템 리스트
            processor_func: 처리 함수
            fail_fast: True면 첫 에러 시 중단, False면 계속 진행

        Returns:
            처리 결과 리스트 (에러는 None 또는 Exception 객체)
        """
        async def process_with_semaphore(item):
            async with self.semaphore:
                try:
                    return await processor_func(item)
                except Exception as e:
                    if fail_fast:
                        raise
                    return e

        tasks = [process_with_semaphore(item) for item in items]

        if fail_fast:
            return await asyncio.gather(*tasks)
        else:
            return await asyncio.gather(*tasks, return_exceptions=True)
```

### 8-2. 이미지 다운로드 최적화

```python
# app/services/media/download_optimizer.py (NEW)
import asyncio
from typing import List, Optional
import httpx

from app.schemas.media import ImageMetadata


class DownloadOptimizer:
    """이미지 다운로드 최적화 전략"""

    @staticmethod
    async def download_with_priority(
        image_urls: List[str],
        priorities: List[int]
    ) -> List[bytes]:
        """
        우선순위에 따른 이미지 다운로드

        전략:
        - 고해상도 이미지 우선
        - 작은 이미지는 건너뛰기 (< 100KB)
        - 실패 시 다음 이미지로
        """
        # 우선순위 정렬
        sorted_items = sorted(
            zip(image_urls, priorities),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url, priority in sorted_items:
                try:
                    # HEAD 요청으로 크기 확인
                    head_response = await client.head(url)
                    content_length = int(head_response.headers.get('content-length', 0))

                    # 너무 작은 이미지는 스킵
                    if content_length < 100 * 1024:  # 100KB
                        continue

                    # 실제 다운로드
                    response = await client.get(url)
                    results.append(response.content)

                    # 최대 3장만
                    if len(results) >= 3:
                        break

                except Exception:
                    continue

        return results

    @staticmethod
    def estimate_download_time(image_urls: List[str]) -> float:
        """
        다운로드 예상 시간 계산

        가정:
        - 평균 이미지 크기: 2MB
        - 평균 다운로드 속도: 10MB/s
        - 처리 오버헤드: 이미지당 0.5초
        """
        num_images = min(len(image_urls), 3)
        download_time = num_images * 2 / 10  # 다운로드: ~0.6초
        processing_time = num_images * 0.5   # 처리: ~1.5초
        return download_time + processing_time  # 총 ~2.1초
```

---

## 9. 테스트 전략 (TDD)

### 9-1. 단위 테스트 예제

```python
# tests/unit/services/media/test_image_processor.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
import io

from app.services.media.image_processor import ImageProcessor
from app.exceptions.media import ImageDownloadError, InvalidImageError


class TestImageProcessor:
    """ImageProcessor 단위 테스트"""

    @pytest.fixture
    async def processor(self):
        """ImageProcessor 픽스처"""
        async with ImageProcessor() as proc:
            yield proc

    @pytest.mark.asyncio
    async def test_download_image_success(self, processor):
        """이미지 다운로드 성공 테스트"""
        # Given
        test_url = "https://example.com/image.jpg"
        mock_image_bytes = self._create_test_image_bytes()

        with patch.object(processor.http_client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = mock_image_bytes
            mock_response.headers = {'content-length': str(len(mock_image_bytes))}
            mock_get.return_value = mock_response

            # When
            result = await processor._download_image(test_url)

            # Then
            assert result == mock_image_bytes
            mock_get.assert_called_once_with(test_url)

    @pytest.mark.asyncio
    async def test_download_image_too_large(self, processor):
        """이미지 크기 초과 시 에러"""
        # Given
        test_url = "https://example.com/huge_image.jpg"
        huge_size = processor.MAX_IMAGE_SIZE_BYTES + 1

        with patch.object(processor.http_client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.headers = {'content-length': str(huge_size)}
            mock_get.return_value = mock_response

            # When/Then
            with pytest.raises(ImageDownloadError, match="too large"):
                await processor._download_image(test_url)

    @pytest.mark.asyncio
    async def test_resize_if_needed_large_image(self, processor):
        """큰 이미지 리사이징"""
        # Given
        large_image = Image.new('RGB', (2000, 2000))

        # When
        resized = await processor._resize_if_needed(large_image)

        # Then
        assert max(resized.size) == processor.TARGET_MAX_DIMENSION
        assert resized.size[0] == resized.size[1]  # 종횡비 유지

    @pytest.mark.asyncio
    async def test_resize_if_needed_small_image(self, processor):
        """작은 이미지는 리사이징 안함"""
        # Given
        small_image = Image.new('RGB', (500, 500))

        # When
        resized = await processor._resize_if_needed(small_image)

        # Then
        assert resized.size == (500, 500)  # 크기 변경 없음

    @pytest.mark.asyncio
    async def test_validate_image_invalid_format(self, processor):
        """지원하지 않는 포맷"""
        # Given
        invalid_image = Image.new('RGB', (100, 100))
        invalid_image.format = 'BMP'  # 지원 안함

        # When/Then
        with pytest.raises(InvalidImageError, match="Unsupported format"):
            await processor._validate_image(invalid_image)

    @pytest.mark.asyncio
    async def test_validate_image_too_small(self, processor):
        """너무 작은 이미지"""
        # Given
        tiny_image = Image.new('RGB', (50, 50))
        tiny_image.format = 'JPEG'

        # When/Then
        with pytest.raises(InvalidImageError, match="too small"):
            await processor._validate_image(tiny_image)

    @pytest.mark.asyncio
    async def test_normalize_format_rgba_to_rgb(self, processor):
        """RGBA를 RGB로 변환"""
        # Given
        rgba_image = Image.new('RGBA', (100, 100), (255, 0, 0, 128))

        # When
        rgb_image = await processor._normalize_format(rgba_image)

        # Then
        assert rgb_image.mode == 'RGB'
        assert rgb_image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_calculate_quality_score_high_quality(self, processor):
        """고품질 이미지 점수"""
        # Given
        hq_image = Image.new('RGB', (1920, 1080))
        file_size = 1920 * 1080 * 2  # ~2 bytes/pixel

        # When
        score = processor._calculate_quality_score(hq_image, file_size)

        # Then
        assert score > 0.7  # 고품질

    @pytest.mark.asyncio
    async def test_calculate_quality_score_low_quality(self, processor):
        """저품질 이미지 점수"""
        # Given
        lq_image = Image.new('RGB', (320, 240))
        file_size = 320 * 240 * 0.3  # 과도한 압축

        # When
        score = processor._calculate_quality_score(lq_image, file_size)

        # Then
        assert score < 0.5  # 저품질

    def _create_test_image_bytes(self) -> bytes:
        """테스트용 이미지 바이너리 생성"""
        img = Image.new('RGB', (500, 500), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()
```

### 9-2. 통합 테스트 예제

```python
# tests/integration/test_multimodal_pipeline.py
import pytest
from httpx import AsyncClient

from app.main import app


class TestMultimodalPipeline:
    """멀티모달 분석 파이프라인 통합 테스트"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_instagram_post_with_images(self):
        """Instagram 게시물 멀티모달 분석 (이미지 포함)"""
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "url": "https://www.instagram.com/p/test123/",
                "force_refresh": False
            }

            # When
            response = await client.post(
                "/api/v1/links/analyze",
                json=request_data
            )

            # Then
            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True
            assert result["analysis_id"] is not None
            assert result["status"] in ["completed", "in_progress"]

            if result["status"] == "completed":
                assert result["result"] is not None
                assert result["result"]["place_info"] is not None
                assert result["result"]["place_info"]["name"] is not None

                # 멀티모달 메타데이터 확인
                if "multimodal_metadata" in result["result"]:
                    metadata = result["result"]["multimodal_metadata"]
                    assert metadata["num_images_analyzed"] > 0
                    assert metadata["ai_inference_time"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_youtube_video(self):
        """YouTube 영상 분석 (썸네일 + 자막)"""
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "url": "https://www.youtube.com/watch?v=test123",
                "force_refresh": False
            }

            # When
            response = await client.post(
                "/api/v1/links/analyze",
                json=request_data
            )

            # Then
            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True

            if result["status"] == "completed":
                metadata = result["result"].get("multimodal_metadata")
                if metadata:
                    # 영상 프레임 또는 썸네일 분석 확인
                    assert (
                        metadata["num_images_analyzed"] > 0 or
                        metadata["num_video_frames"] > 0
                    )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fallback_to_text_only_on_image_failure(self):
        """이미지 실패 시 텍스트 기반 Fallback"""
        # Given: 이미지 URL이 잘못된 경우
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "url": "https://www.instagram.com/p/invalid_post/",
                "force_refresh": True
            }

            # When
            response = await client.post(
                "/api/v1/links/analyze",
                json=request_data
            )

            # Then: 텍스트 기반으로라도 분석 완료
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                result = response.json()
                # Fallback 모드 확인
                if result.get("result"):
                    metadata = result["result"].get("multimodal_metadata")
                    if metadata:
                        assert metadata["num_images_analyzed"] == 0  # 이미지 실패
```

### 9-3. 성능 테스트

```python
# tests/performance/test_image_processing_performance.py
import pytest
import time
from PIL import Image

from app.services.media.image_processor import ImageProcessor


class TestImageProcessingPerformance:
    """이미지 처리 성능 테스트"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_image_download_time(self):
        """이미지 3장 다운로드 시간 측정"""
        # Given
        test_urls = [
            "https://picsum.photos/1024/1024",
            "https://picsum.photos/1024/768",
            "https://picsum.photos/800/600",
        ]

        # When
        start_time = time.time()
        async with ImageProcessor() as processor:
            pil_images, processed_images = await processor.download_and_process_images(
                test_urls,
                max_images=3
            )
        elapsed_time = time.time() - start_time

        # Then
        assert len(pil_images) <= 3
        assert elapsed_time < 5.0  # 5초 이내 (목표: 3초)

        print(f"\n✅ Downloaded {len(pil_images)} images in {elapsed_time:.2f}s")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multimodal_analysis_time(self):
        """멀티모달 분석 전체 시간 측정"""
        # Given
        from app.services.places.multimodal_orchestrator import MultimodalOrchestrator
        from app.schemas.content import ContentMetadata

        orchestrator = MultimodalOrchestrator()
        content = ContentMetadata(
            title="성수동 브런치 카페",
            description="오늘의 힐링 공간",
            images=[
                "https://picsum.photos/1024/1024",
                "https://picsum.photos/800/600",
            ],
            hashtags=["카페", "성수동", "브런치"]
        )

        # When
        start_time = time.time()
        place_info, confidence, metadata = await orchestrator.analyze_content(
            content,
            enable_image_analysis=True,
            max_images=2
        )
        elapsed_time = time.time() - start_time

        # Then
        assert elapsed_time < 15.0  # 15초 이내 (목표)
        assert metadata.num_images_analyzed > 0

        print(f"\n✅ Multimodal analysis completed in {elapsed_time:.2f}s")
        print(f"   - Images analyzed: {metadata.num_images_analyzed}")
        print(f"   - AI inference: {metadata.ai_inference_time:.2f}s")
        print(f"   - Image processing: {metadata.image_processing_time:.2f}s")
```

---

## 10. 모니터링 및 메트릭

### 10-1. Prometheus 메트릭 정의

```python
# app/services/monitoring/multimodal_metrics.py (NEW)
from prometheus_client import Counter, Histogram, Gauge, Summary

# 멀티모달 분석 요청 수
multimodal_analysis_requests_total = Counter(
    'multimodal_analysis_requests_total',
    'Total multimodal analysis requests',
    ['platform', 'has_images', 'status']
)

# 이미지 다운로드 성공/실패
image_download_total = Counter(
    'image_download_total',
    'Total image download attempts',
    ['status']  # success, failed, timeout
)

# 이미지 처리 시간
image_processing_duration_seconds = Histogram(
    'image_processing_duration_seconds',
    'Image processing duration',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# AI 추론 시간 (멀티모달)
ai_inference_duration_seconds = Histogram(
    'ai_inference_multimodal_duration_seconds',
    'AI inference duration for multimodal analysis',
    ['num_images'],
    buckets=[1.0, 3.0, 5.0, 10.0, 20.0, 60.0]
)

# 신뢰도 분포
confidence_score_distribution = Histogram(
    'confidence_score_distribution',
    'Distribution of confidence scores',
    ['analysis_type'],  # text_only, multimodal
    buckets=[0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# 이미지 품질 평균
avg_image_quality_gauge = Gauge(
    'avg_image_quality',
    'Average image quality score'
)

# Fallback 발생 횟수
fallback_events_total = Counter(
    'fallback_events_total',
    'Total fallback events',
    ['reason']  # image_download_failed, image_processing_failed, ai_error
)


class MultimodalMetricsCollector:
    """멀티모달 분석 메트릭 수집"""

    @staticmethod
    def record_analysis_request(
        platform: str,
        has_images: bool,
        status: str
    ):
        """분석 요청 기록"""
        multimodal_analysis_requests_total.labels(
            platform=platform,
            has_images=str(has_images),
            status=status
        ).inc()

    @staticmethod
    def record_image_download(status: str):
        """이미지 다운로드 결과 기록"""
        image_download_total.labels(status=status).inc()

    @staticmethod
    def record_image_processing_time(duration: float):
        """이미지 처리 시간 기록"""
        image_processing_duration_seconds.observe(duration)

    @staticmethod
    def record_ai_inference_time(duration: float, num_images: int):
        """AI 추론 시간 기록"""
        ai_inference_duration_seconds.labels(
            num_images=str(num_images)
        ).observe(duration)

    @staticmethod
    def record_confidence_score(score: float, analysis_type: str):
        """신뢰도 점수 기록"""
        confidence_score_distribution.labels(
            analysis_type=analysis_type
        ).observe(score)

    @staticmethod
    def update_avg_image_quality(quality: float):
        """평균 이미지 품질 업데이트"""
        avg_image_quality_gauge.set(quality)

    @staticmethod
    def record_fallback_event(reason: str):
        """Fallback 이벤트 기록"""
        fallback_events_total.labels(reason=reason).inc()
```

### 10-2. 로깅 전략

```python
# app/services/monitoring/multimodal_logger.py (NEW)
import logging
import structlog
from typing import Dict, Any

logger = structlog.get_logger()


class MultimodalAnalysisLogger:
    """멀티모달 분석 구조화 로깅"""

    @staticmethod
    def log_analysis_start(
        analysis_id: str,
        url: str,
        num_images: int,
        enable_image_analysis: bool
    ):
        """분석 시작 로그"""
        logger.info(
            "multimodal_analysis_started",
            analysis_id=analysis_id,
            url_hash=_hash_url(url),
            num_images_provided=num_images,
            image_analysis_enabled=enable_image_analysis
        )

    @staticmethod
    def log_image_processing(
        analysis_id: str,
        num_images_processed: int,
        num_images_failed: int,
        processing_time: float
    ):
        """이미지 처리 로그"""
        logger.info(
            "image_processing_completed",
            analysis_id=analysis_id,
            images_processed=num_images_processed,
            images_failed=num_images_failed,
            processing_time_seconds=processing_time,
            success_rate=num_images_processed / (num_images_processed + num_images_failed)
                if (num_images_processed + num_images_failed) > 0 else 0
        )

    @staticmethod
    def log_ai_inference(
        analysis_id: str,
        num_images_analyzed: int,
        inference_time: float,
        confidence: float
    ):
        """AI 추론 로그"""
        logger.info(
            "ai_inference_completed",
            analysis_id=analysis_id,
            num_images_analyzed=num_images_analyzed,
            inference_time_seconds=inference_time,
            confidence_score=confidence
        )

    @staticmethod
    def log_analysis_complete(
        analysis_id: str,
        total_time: float,
        confidence: float,
        metadata: Dict[str, Any]
    ):
        """분석 완료 로그"""
        logger.info(
            "multimodal_analysis_completed",
            analysis_id=analysis_id,
            total_time_seconds=total_time,
            final_confidence=confidence,
            metadata=metadata
        )

    @staticmethod
    def log_fallback_event(
        analysis_id: str,
        reason: str,
        fallback_strategy: str
    ):
        """Fallback 이벤트 로그"""
        logger.warning(
            "fallback_triggered",
            analysis_id=analysis_id,
            reason=reason,
            fallback_strategy=fallback_strategy
        )


def _hash_url(url: str) -> str:
    """URL 해시 (로깅용)"""
    import hashlib
    return hashlib.sha256(url.encode()).hexdigest()[:16]
```

---

## 11. 보안 및 개인정보

### 11-1. 이미지 보안 검증

```python
# app/services/media/security_validator.py (NEW)
from PIL import Image
from typing import List
import re


class MediaSecurityValidator:
    """미디어 보안 검증"""

    # 허용된 도메인 (화이트리스트)
    ALLOWED_IMAGE_DOMAINS = {
        'instagram.com',
        'cdninstagram.com',
        'fbcdn.net',
        'youtube.com',
        'ytimg.com',
        'googleusercontent.com',
        'pstatic.net',  # Naver
        'kakaocdn.net'
    }

    @staticmethod
    def validate_image_url(url: str) -> bool:
        """이미지 URL 보안 검증"""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)

            # 1. 프로토콜 검증
            if parsed.scheme not in ['http', 'https']:
                return False

            # 2. 도메인 화이트리스트 검증
            domain = parsed.netloc.lower()
            if not any(allowed in domain for allowed in MediaSecurityValidator.ALLOWED_IMAGE_DOMAINS):
                return False

            # 3. 파일 확장자 검증
            path = parsed.path.lower()
            if not any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def scan_image_for_sensitive_content(image: Image.Image) -> bool:
        """이미지에서 민감한 콘텐츠 감지 (간단한 휴리스틱)"""
        # TODO: 실제 구현에서는 ML 모델 사용
        # 여기서는 기본 검증만

        width, height = image.size

        # 너무 작거나 큰 이미지 의심
        if width < 50 or height < 50:
            return False  # 1x1 픽셀 트래킹 이미지 등

        if width > 10000 or height > 10000:
            return False  # DoS 공격 의심

        return True

    @staticmethod
    def sanitize_exif_data(image: Image.Image) -> Image.Image:
        """EXIF 데이터에서 개인정보 제거"""
        # GPS 정보는 분석에만 사용하고 저장 안함
        # 새 이미지 생성 (EXIF 없음)

        new_image = Image.new(image.mode, image.size)
        new_image.putdata(list(image.getdata()))

        return new_image
```

### 11-2. 개인정보 마스킹

```python
# app/services/media/privacy_filter.py (NEW)
import re
from typing import Optional


class PrivacyFilter:
    """개인정보 필터링 및 마스킹"""

    @staticmethod
    def mask_phone_number(text: str) -> str:
        """전화번호 마스킹"""
        # 010-1234-5678 → 010-****-5678
        return re.sub(
            r'(\d{2,3})-(\d{3,4})-(\d{4})',
            r'\1-****-\3',
            text
        )

    @staticmethod
    def mask_email(text: str) -> str:
        """이메일 마스킹"""
        # user@example.com → u***@example.com
        return re.sub(
            r'\b([a-zA-Z0-9])[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'\1***@\2',
            text
        )

    @staticmethod
    def filter_sensitive_data(text: str) -> str:
        """종합 민감 데이터 필터링"""
        text = PrivacyFilter.mask_phone_number(text)
        text = PrivacyFilter.mask_email(text)
        return text

    @staticmethod
    def should_cache_content(text: str) -> bool:
        """캐싱 가능 여부 판단"""
        # 전화번호/이메일 포함 시 캐싱 금지
        has_phone = bool(re.search(r'\d{2,3}-\d{3,4}-\d{4}', text))
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))

        return not (has_phone or has_email)
```

---

## 12. 배포 및 운영

### 12-1. 환경 변수 설정

```bash
# .env.multimodal (NEW)

# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60

# 이미지 처리 설정
MAX_IMAGE_SIZE_MB=10
MAX_IMAGES_PER_ANALYSIS=3
IMAGE_DOWNLOAD_TIMEOUT=10
IMAGE_PROCESSING_WORKERS=3

# 캐시 설정
REDIS_URL=redis://localhost:6379/0
IMAGE_CACHE_TTL=3600
MULTIMODAL_CACHE_TTL=2592000  # 30일

# 성능 설정
ENABLE_IMAGE_ANALYSIS=true
ENABLE_VIDEO_ANALYSIS=true
PARALLEL_IMAGE_DOWNLOADS=3

# 모니터링
PROMETHEUS_ENABLED=true
STRUCTURED_LOGGING=true
```

### 12-2. Docker 구성

```dockerfile
# Dockerfile.multimodal
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (이미지 처리용)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pillow 최적화 빌드 확인
RUN python -c "from PIL import Image; print(Image.PILLOW_VERSION)"

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12-3. Kubernetes 배포

```yaml
# k8s/multimodal-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multimodal-analysis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multimodal-analysis
  template:
    metadata:
      labels:
        app: multimodal-analysis
    spec:
      containers:
      - name: multimodal
        image: hotly/multimodal-analysis:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
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
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## 13. API 문서

### 13-1. 멀티모달 분석 API

```python
# OpenAPI 스키마 (자동 생성)

@router.post("/analyze", response_model=LinkAnalyzeResponse)
async def analyze_link_multimodal(
    request: LinkAnalyzeRequestMultimodal,
    background_tasks: BackgroundTasks
):
    """
    ## 멀티모달 SNS 링크 분석

    **기능:**
    - 텍스트 + 이미지 + 영상을 종합 분석
    - 간판 인식, 메뉴판 OCR
    - 신뢰도 점수 및 분석 근거 제공

    **지원 플랫폼:**
    - Instagram (게시물, 릴스)
    - YouTube (일반 영상, Shorts)
    - Naver Blog

    **처리 시간:**
    - 캐시 적중: < 1초
    - 텍스트만: ~ 5초
    - 이미지 1-3장: ~ 15초

    **요청 예시:**
    ```json
    {
      "url": "https://www.instagram.com/p/xyz123/",
      "force_refresh": false,
      "enable_image_analysis": true,
      "max_images_to_analyze": 3,
      "include_reasoning": true
    }
    ```

    **응답 예시:**
    ```json
    {
      "success": true,
      "analysis_id": "uuid",
      "status": "completed",
      "result": {
        "place_info": {
          "name": "카페 오아시스",
          "address": "서울 성동구 성수동",
          "category": ["카페", "브런치"],
          "confidence": 0.95
        },
        "multimodal_metadata": {
          "num_images_analyzed": 3,
          "ai_inference_time": 8.5,
          "confidence_factors": {
            "signboard_detected": 0.95,
            "image_quality": 0.90
          },
          "reasoning": "이미지 속 간판에서 '카페 오아시스' 인식"
        }
      },
      "cached": false,
      "processing_time": 12.3
    }
    ```
    """
    pass
```

---

## 14. 비용 최적화 전략

### 14-1. Gemini API 비용 분석

```
Gemini 2.0 Flash 가격 (2025년 기준):
- 텍스트만: $0.075 / 1M input tokens
- 이미지 포함: +$0.00025 / image (1024x1024 기준)

예상 비용:
- 텍스트 분석 (1000 tokens): $0.000075
- 이미지 3장 분석: $0.00075
- 총: $0.000825 per request

월 10,000 요청 시:
- 캐시 적중률 50% 가정
- 실제 AI 호출: 5,000 requests
- 월 비용: 5,000 * $0.000825 = $4.13
```

### 14-2. 비용 절감 전략

```python
# app/services/ai/cost_optimizer.py (NEW)

class CostOptimizer:
    """API 비용 최적화"""

    @staticmethod
    def should_analyze_images(
        confidence_from_text: float,
        num_images: int,
        user_tier: str
    ) -> bool:
        """
        이미지 분석 필요성 판단

        전략:
        - 텍스트 신뢰도가 높으면 이미지 스킵
        - 이미지 개수가 많으면 선택적 분석
        - 사용자 등급에 따라 제한
        """
        # 텍스트 신뢰도가 매우 높으면 이미지 불필요
        if confidence_from_text > 0.9:
            return False

        # Free 사용자는 이미지 1장만
        if user_tier == "free" and num_images > 1:
            return False

        return True

    @staticmethod
    def select_images_to_analyze(
        image_urls: List[str],
        max_images: int,
        prioritize_by: str = "quality"
    ) -> List[str]:
        """
        분석할 이미지 선택

        우선순위:
        - quality: 고해상도 우선
        - position: 첫 번째 이미지 우선
        - random: 랜덤 선택
        """
        if prioritize_by == "position":
            return image_urls[:max_images]

        # TODO: quality 기반 선택 구현
        return image_urls[:max_images]
```

---

## 15. 용어 사전

- **멀티모달 (Multimodal)**: 텍스트, 이미지, 영상 등 여러 형태의 데이터를 동시에 처리하는 AI 기법
- **PIL.Image**: Python Imaging Library의 이미지 객체
- **EXIF**: 이미지 파일에 포함된 메타데이터 (GPS, 촬영 시간 등)
- **OCR**: Optical Character Recognition, 이미지 속 텍스트 인식
- **Fallback**: 주요 기능 실패 시 대체 방법으로 처리
- **Confidence Score**: AI 분석 결과의 신뢰도 점수 (0.0~1.0)
- **Orchestrator**: 여러 서비스를 조율하는 통합 관리자
- **Semaphore**: 동시 실행 개수를 제한하는 동기화 메커니즘

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- 2025-01-XX: 섹션 4-4 ~ 15 완성 (오케스트레이터, 프롬프트, 테스팅, 모니터링, 보안, 배포, API 문서, 비용 최적화)
- PRD 12-multimodal 버전과 연동
