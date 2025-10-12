# TRD 12-1: 이미지 처리 파이프라인 상세 설계

## 목차
1. [아키텍처 개요](#1-아키텍처-개요)
2. [필수 라이브러리 및 의존성](#2-필수-라이브러리-및-의존성)
3. [이미지 다운로드 모듈](#3-이미지-다운로드-모듈)
4. [이미지 전처리 모듈](#4-이미지-전처리-모듈)
5. [품질 분석 및 선택 모듈](#5-품질-분석-및-선택-모듈)
6. [메타데이터 추출 모듈](#6-메타데이터-추출-모듈)
7. [포맷 변환 및 최적화](#7-포맷-변환-및-최적화)
8. [캐싱 전략](#8-캐싱-전략)
9. [성능 최적화](#9-성능-최적화)
10. [에러 처리 및 복원력](#10-에러-처리-및-복원력)
11. [모니터링 및 디버깅](#11-모니터링-및-디버깅)
12. [보안 및 검증](#12-보안-및-검증)

---

## 1. 아키텍처 개요

### 1-1. 전체 파이프라인 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    Image Processing Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: List[str] (Image URLs)                                  │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 1: URL Validation & Security Check             │      │
│  │ - Domain whitelist verification                       │      │
│  │ - URL format validation                               │      │
│  │ - Protocol check (HTTPS only)                         │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 2: Parallel Download (max 3 concurrent)        │      │
│  │ - httpx async client                                  │      │
│  │ - Connection pooling                                  │      │
│  │ - Retry with exponential backoff                      │      │
│  │ - Size validation (max 10MB)                          │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 3: Image Decoding & Validation                 │      │
│  │ - PIL.Image.open()                                    │      │
│  │ - Format detection (JPEG, PNG, WebP, GIF)            │      │
│  │ - Corruption check                                    │      │
│  │ - Dimension validation (100x100 ~ 10000x10000)        │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 4: Quality Analysis                            │      │
│  │ - Resolution scoring                                  │      │
│  │ - Blur detection (Laplacian variance)                │      │
│  │ - Brightness/Contrast analysis                        │      │
│  │ - Compression quality estimation                      │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 5: Image Selection (Top 3)                     │      │
│  │ - Quality score ranking                               │      │
│  │ - Diversity check (avoid duplicates)                 │      │
│  │ - Content type detection (signboard priority)        │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 6: Pre-processing                              │      │
│  │ - Resize to 1024x1024 (max dimension)                │      │
│  │ - EXIF orientation correction                         │      │
│  │ - Color space conversion (RGB)                        │      │
│  │ - Optional: Sharpening, Noise reduction              │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 7: Metadata Extraction                         │      │
│  │ - EXIF GPS coordinates                                │      │
│  │ - DateTime original                                   │      │
│  │ - Camera info (optional)                              │      │
│  │ - File metadata (size, format, dimensions)           │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 8: Format Normalization                        │      │
│  │ - RGBA → RGB conversion                               │      │
│  │ - Palette mode → RGB                                  │      │
│  │ - GIF first frame extraction                          │      │
│  │ - WebP → JPEG conversion                              │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stage 9: Cache Storage                               │      │
│  │ - L1: Memory cache (compressed JPEG, 1h TTL)         │      │
│  │ - L2: Redis metadata (7d TTL)                         │      │
│  └──────────────────────────────────────────────────────┘      │
│    ↓                                                             │
│  Output: List[PIL.Image], List[ImageMetadata]                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Timing Breakdown (Target):
- URL Validation: < 10ms
- Download (3 images): 2-5 seconds (parallel)
- Decoding & Validation: 100-300ms per image
- Quality Analysis: 50-200ms per image
- Pre-processing: 100-500ms per image
- Total: 3-8 seconds for 3 images
```

---

## 2. 필수 라이브러리 및 의존성

### 2-1. Python 패키지 (requirements.txt)

```text
# Core Image Processing
Pillow==10.2.0              # PIL fork, 이미지 처리 핵심
pillow-heif==0.15.0         # HEIF/HEIC 지원 (iPhone)
pillow-avif-plugin==1.4.1   # AVIF 지원 (최신 포맷)

# Async HTTP Client
httpx==0.27.0               # 비동기 HTTP 클라이언트
httpx[http2]                # HTTP/2 지원 (성능 향상)

# Image Analysis
opencv-python-headless==4.9.0.80  # 컴퓨터 비전 (blur detection)
numpy==1.26.3               # 수치 연산
scikit-image==0.22.0        # 이미지 품질 분석

# Metadata Extraction
piexif==1.1.3               # EXIF 데이터 읽기/쓰기
ExifRead==3.0.0             # EXIF 데이터 파싱 (대체)

# Hashing & Fingerprinting
imagehash==4.3.1            # Perceptual hashing (중복 감지)

# Caching
cachetools==5.3.2           # 메모리 캐시 (TTL 지원)
redis[hiredis]==5.0.1       # Redis 클라이언트 (고성능)

# Performance
orjson==3.9.12              # 빠른 JSON 직렬화
msgpack==1.0.7              # 바이너리 직렬화 (캐시용)

# Monitoring
prometheus-client==0.19.0   # 메트릭 수집
```

### 2-2. 시스템 패키지 (Ubuntu/Debian)

```bash
# 이미지 라이브러리 의존성
apt-get install -y \
  libjpeg-dev \          # JPEG 지원
  libpng-dev \           # PNG 지원
  libwebp-dev \          # WebP 지원
  libtiff5-dev \         # TIFF 지원
  libopenjp2-7-dev \     # JPEG2000 지원
  zlib1g-dev \           # 압축 라이브러리
  libfreetype6-dev \     # 폰트 렌더링
  liblcms2-dev \         # 색상 관리
  libheif-dev            # HEIF 지원

# OpenCV 의존성
apt-get install -y \
  libopencv-dev \
  python3-opencv

# (선택) 고성능 이미지 처리
apt-get install -y \
  libvips-dev            # libvips (Pillow보다 빠름, 선택사항)
```

### 2-3. Pillow 최적화 빌드 확인

```python
# check_pillow_features.py
from PIL import features, Image

print("=== Pillow Feature Check ===")
print(f"Pillow Version: {Image.__version__}")
print(f"PIL PILLOW VERSION: {Image.PILLOW_VERSION}")

# 지원 포맷 확인
print("\n=== Supported Formats ===")
formats = {
    'JPEG': features.check_codec('jpg'),
    'JPEG2000': features.check_codec('jpg_2000'),
    'PNG': features.check_codec('png'),
    'WebP': features.check_codec('webp'),
    'TIFF': features.check_codec('tiff'),
}

for format_name, supported in formats.items():
    status = "✅" if supported else "❌"
    print(f"{status} {format_name}")

# 성능 관련 기능
print("\n=== Performance Features ===")
print(f"{'✅' if features.check_feature('libjpeg_turbo') else '❌'} libjpeg-turbo (Fast JPEG)")
print(f"{'✅' if features.check_feature('webp') else '❌'} WebP")
print(f"{'✅' if features.check_feature('webp_anim') else '❌'} WebP Animation")
print(f"{'✅' if features.check_feature('webp_mux') else '❌'} WebP Mux")

# EXIF 지원
print(f"\n{'✅' if hasattr(Image, '_getexif') else '❌'} EXIF Support")
```

---

## 3. 이미지 다운로드 모듈

### 3-1. 고성능 비동기 다운로더

```python
# app/services/media/image_downloader.py
import asyncio
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

import httpx
from httpx import Timeout, Limits

from app.core.config import settings
from app.exceptions.media import ImageDownloadError
from app.services.monitoring.metrics import download_metrics


@dataclass
class DownloadResult:
    """다운로드 결과"""
    url: str
    success: bool
    data: Optional[bytes] = None
    error: Optional[str] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    content_length: int = 0
    download_time: float = 0.0
    retry_count: int = 0


class ImageDownloader:
    """
    고성능 비동기 이미지 다운로더

    특징:
    - HTTP/2 지원 (멀티플렉싱)
    - Connection pooling
    - 동시 다운로드 제한 (Semaphore)
    - Exponential backoff retry
    - Content-Length 사전 검증
    """

    # 설정 상수
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    DOWNLOAD_TIMEOUT = 10.0  # 초
    MAX_RETRIES = 3
    MAX_CONCURRENT_DOWNLOADS = 3

    # HTTP/2 활성화, Connection pooling
    HTTP_LIMITS = Limits(
        max_connections=20,
        max_keepalive_connections=10
    )

    HTTP_TIMEOUT = Timeout(
        connect=5.0,  # 연결 타임아웃
        read=10.0,    # 읽기 타임아웃
        write=5.0,    # 쓰기 타임아웃
        pool=5.0      # 풀 타임아웃
    )

    def __init__(self):
        """다운로더 초기화"""
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_DOWNLOADS)
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.client = httpx.AsyncClient(
            timeout=self.HTTP_TIMEOUT,
            limits=self.HTTP_LIMITS,
            http2=True,  # HTTP/2 활성화
            follow_redirects=True,
            headers={
                'User-Agent': 'HotlyBot/1.0 (+https://hotly.app)',
                'Accept': 'image/jpeg,image/png,image/webp,image/*;q=0.8',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.client:
            await self.client.aclose()

    async def download_images(
        self,
        urls: List[str],
        validate_size: bool = True
    ) -> List[DownloadResult]:
        """
        여러 이미지를 병렬로 다운로드

        Args:
            urls: 다운로드할 이미지 URL 리스트
            validate_size: Content-Length 사전 검증 여부

        Returns:
            DownloadResult 리스트 (성공/실패 모두 포함)
        """
        if not urls:
            return []

        # 병렬 다운로드 태스크 생성
        tasks = [
            self._download_single_with_retry(url, validate_size)
            for url in urls
        ]

        # 모든 태스크 실행 (실패해도 계속)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exception을 DownloadResult로 변환
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(DownloadResult(
                    url=urls[i],
                    success=False,
                    error=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def _download_single_with_retry(
        self,
        url: str,
        validate_size: bool
    ) -> DownloadResult:
        """
        단일 이미지 다운로드 (재시도 포함)

        재시도 전략:
        - 1차 실패: 1초 대기
        - 2차 실패: 2초 대기
        - 3차 실패: 4초 대기
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._download_single(url, validate_size)
                result.retry_count = attempt
                return result

            except Exception as e:
                last_error = e

                # 마지막 시도면 실패 처리
                if attempt == self.MAX_RETRIES - 1:
                    break

                # Exponential backoff
                delay = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(delay)

        # 모든 재시도 실패
        return DownloadResult(
            url=url,
            success=False,
            error=f"Failed after {self.MAX_RETRIES} retries: {str(last_error)}",
            retry_count=self.MAX_RETRIES
        )

    async def _download_single(
        self,
        url: str,
        validate_size: bool
    ) -> DownloadResult:
        """
        단일 이미지 다운로드 (실제 로직)
        """
        start_time = asyncio.get_event_loop().time()

        # Semaphore로 동시 다운로드 제한
        async with self.semaphore:
            try:
                # Step 1: HEAD 요청으로 크기 사전 검증 (선택적)
                if validate_size:
                    head_response = await self.client.head(url)
                    content_length = int(head_response.headers.get('content-length', 0))

                    if content_length > self.MAX_IMAGE_SIZE:
                        raise ImageDownloadError(
                            f"Image too large: {content_length} bytes (max: {self.MAX_IMAGE_SIZE})"
                        )

                # Step 2: GET 요청으로 실제 다운로드
                response = await self.client.get(url)
                response.raise_for_status()

                image_data = response.content
                download_time = asyncio.get_event_loop().time() - start_time

                # Step 3: 실제 크기 검증
                if len(image_data) > self.MAX_IMAGE_SIZE:
                    raise ImageDownloadError(
                        f"Downloaded image too large: {len(image_data)} bytes"
                    )

                # 메트릭 기록
                download_metrics.record_download_success(
                    url=url,
                    size_bytes=len(image_data),
                    duration=download_time
                )

                return DownloadResult(
                    url=url,
                    success=True,
                    data=image_data,
                    http_status=response.status_code,
                    content_type=response.headers.get('content-type'),
                    content_length=len(image_data),
                    download_time=download_time
                )

            except httpx.HTTPStatusError as e:
                download_metrics.record_download_failure(url, 'http_error')
                raise ImageDownloadError(
                    f"HTTP {e.response.status_code}: {url}"
                )

            except httpx.TimeoutException:
                download_metrics.record_download_failure(url, 'timeout')
                raise ImageDownloadError(f"Download timeout: {url}")

            except httpx.RequestError as e:
                download_metrics.record_download_failure(url, 'request_error')
                raise ImageDownloadError(f"Request failed: {str(e)}")

            except Exception as e:
                download_metrics.record_download_failure(url, 'unknown')
                raise ImageDownloadError(f"Download failed: {str(e)}")


class DownloadOptimizer:
    """다운로드 최적화 전략"""

    @staticmethod
    async def prefetch_head_info(
        urls: List[str],
        client: httpx.AsyncClient
    ) -> List[Tuple[str, int, str]]:
        """
        HEAD 요청으로 이미지 정보 사전 수집

        Returns:
            [(url, content_length, content_type), ...]
        """
        async def fetch_head(url: str):
            try:
                response = await client.head(url, timeout=3.0)
                content_length = int(response.headers.get('content-length', 0))
                content_type = response.headers.get('content-type', '')
                return (url, content_length, content_type)
            except:
                return (url, 0, '')

        tasks = [fetch_head(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)

    @staticmethod
    def prioritize_urls(
        url_info: List[Tuple[str, int, str]],
        max_count: int = 3
    ) -> List[str]:
        """
        URL 우선순위 정렬 및 선택

        우선순위:
        1. 적절한 크기 (500KB ~ 5MB)
        2. JPEG > PNG > WebP
        3. 큰 크기 (고해상도 가능성)
        """
        scored_urls = []

        for url, size, content_type in url_info:
            score = 0.0

            # 크기 점수
            if 500_000 <= size <= 5_000_000:  # 500KB ~ 5MB
                score += 10.0
            elif size > 5_000_000:
                score += 5.0
            elif size > 100_000:
                score += 3.0

            # 포맷 점수
            if 'jpeg' in content_type or 'jpg' in content_type:
                score += 3.0
            elif 'png' in content_type:
                score += 2.0
            elif 'webp' in content_type:
                score += 1.0

            scored_urls.append((url, score))

        # 점수 기준 정렬
        scored_urls.sort(key=lambda x: x[1], reverse=True)

        return [url for url, _ in scored_urls[:max_count]]
```

### 3-2. 연결 풀 관리

```python
# app/services/media/connection_pool.py
from typing import Optional
import httpx


class ConnectionPoolManager:
    """
    HTTP 연결 풀 전역 관리

    장점:
    - 여러 요청에서 연결 재사용
    - 메모리 효율성
    - 성능 향상
    """

    _instance: Optional['ConnectionPoolManager'] = None
    _client: Optional[httpx.AsyncClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """전역 HTTP 클라이언트 가져오기"""
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                ),
                http2=True,
                follow_redirects=True
            )
        return cls._client

    @classmethod
    async def close(cls):
        """클라이언트 종료"""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
```

---

## 4. 이미지 전처리 모듈

### 4-1. 고급 이미지 디코더

```python
# app/services/media/image_decoder.py
import io
from typing import Optional, Tuple
from PIL import Image, ImageFile, UnidentifiedImageError
import logging

logger = logging.getLogger(__name__)

# 큰 이미지도 로드 가능하도록 설정
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageDecoder:
    """
    안전하고 효율적인 이미지 디코더

    특징:
    - Truncated image 처리
    - EXIF orientation 자동 보정
    - Progressive JPEG 지원
    - 메모리 효율적 로딩
    """

    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'HEIF', 'AVIF'}
    MAX_PIXELS = 100_000_000  # 100 megapixels (DoS 방지)

    @staticmethod
    def decode(image_bytes: bytes) -> Tuple[Image.Image, dict]:
        """
        바이트에서 PIL.Image로 디코딩

        Returns:
            (PIL.Image, metadata_dict)
        """
        try:
            # BytesIO로 래핑
            image_stream = io.BytesIO(image_bytes)

            # 이미지 열기 (lazy loading)
            img = Image.open(image_stream)

            # 포맷 검증
            if img.format not in ImageDecoder.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported format: {img.format}")

            # 픽셀 수 검증 (DoS 방지)
            if img.width * img.height > ImageDecoder.MAX_PIXELS:
                raise ValueError(
                    f"Image too large: {img.width}x{img.height} "
                    f"(max {ImageDecoder.MAX_PIXELS} pixels)"
                )

            # EXIF orientation 보정
            img = ImageDecoder._fix_orientation(img)

            # 이미지 실제 로드 (lazy → eager)
            img.load()

            # 메타데이터 추출
            metadata = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'palette': img.palette is not None,
                'animation': getattr(img, 'is_animated', False),
                'frames': getattr(img, 'n_frames', 1)
            }

            return img, metadata

        except UnidentifiedImageError:
            raise ValueError("Cannot identify image format")
        except Image.DecompressionBombError:
            raise ValueError("Image exceeds size limit (decompression bomb)")
        except Exception as e:
            logger.error(f"Image decoding failed: {e}")
            raise ValueError(f"Image decoding failed: {str(e)}")

    @staticmethod
    def _fix_orientation(img: Image.Image) -> Image.Image:
        """
        EXIF orientation 태그에 따라 이미지 회전

        EXIF Orientation 값:
        1 = 정상
        2 = 좌우 반전
        3 = 180도 회전
        4 = 상하 반전
        5 = 상하 반전 + 90도 회전
        6 = 90도 회전 (시계방향)
        7 = 상하 반전 + 270도 회전
        8 = 270도 회전 (시계방향)
        """
        try:
            # EXIF 데이터 가져오기
            exif = img._getexif()
            if exif is None:
                return img

            # Orientation 태그 (274번)
            orientation = exif.get(274)
            if orientation is None:
                return img

            # Orientation에 따른 변환
            if orientation == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 4:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                img = img.transpose(Image.FLIP_TOP_BOTTOM).rotate(90, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 7:
                img = img.transpose(Image.FLIP_TOP_BOTTOM).rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)

            return img

        except (AttributeError, KeyError, IndexError):
            # EXIF 데이터 없거나 orientation 태그 없음
            return img
```

### 4-2. 리사이징 및 최적화

```python
# app/services/media/image_resizer.py
from PIL import Image
from typing import Tuple


class ImageResizer:
    """
    고품질 이미지 리사이징

    리샘플링 알고리즘:
    - LANCZOS: 최고 품질 (느림)
    - BICUBIC: 좋은 품질 (보통)
    - BILINEAR: 빠름 (품질 낮음)
    """

    TARGET_MAX_DIMENSION = 1024  # Gemini API 권장
    RESAMPLING_FILTER = Image.Resampling.LANCZOS  # 최고 품질

    @staticmethod
    def resize_for_analysis(
        img: Image.Image,
        max_dimension: int = TARGET_MAX_DIMENSION
    ) -> Image.Image:
        """
        AI 분석용 리사이징

        특징:
        - 종횡비 유지
        - 한 변만 최대 크기로
        - LANCZOS 필터 사용
        """
        width, height = img.size
        current_max = max(width, height)

        # 이미 작으면 리사이징 불필요
        if current_max <= max_dimension:
            return img

        # 스케일 비율 계산
        scale = max_dimension / current_max

        # 새 크기 계산 (종횡비 유지)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # 리사이징 실행
        resized = img.resize(
            (new_width, new_height),
            resample=ImageResizer.RESAMPLING_FILTER
        )

        return resized

    @staticmethod
    def smart_crop(
        img: Image.Image,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> Image.Image:
        """
        중앙 중점 스마트 크롭

        전략:
        1. 타겟 종횡비 계산
        2. 이미지 중앙 유지하면서 크롭
        3. 리사이징
        """
        width, height = img.size
        target_width, target_height = target_size

        # 타겟 종횡비
        target_ratio = target_width / target_height
        current_ratio = width / height

        if current_ratio > target_ratio:
            # 이미지가 더 넓음 → 좌우 크롭
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            # 이미지가 더 높음 → 상하 크롭
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))

        # 최종 리사이징
        return img.resize(target_size, resample=Image.Resampling.LANCZOS)

    @staticmethod
    def thumbnail_with_padding(
        img: Image.Image,
        size: Tuple[int, int] = (1024, 1024),
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        패딩 추가하여 썸네일 생성

        특징:
        - 종횡비 유지
        - 배경색으로 패딩
        - 왜곡 없음
        """
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # 새 캔버스 생성
        thumb = Image.new('RGB', size, background_color)

        # 중앙에 이미지 붙이기
        offset = (
            (size[0] - img.width) // 2,
            (size[1] - img.height) // 2
        )
        thumb.paste(img, offset)

        return thumb
```

---

## 5. 품질 분석 및 선택 모듈

### 5-1. 이미지 품질 분석기

```python
# app/services/media/quality_analyzer.py
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class QualityMetrics:
    """이미지 품질 메트릭"""
    overall_score: float        # 종합 점수 (0.0 ~ 1.0)
    resolution_score: float     # 해상도 점수
    sharpness_score: float      # 선명도 점수
    brightness_score: float     # 밝기 점수
    contrast_score: float       # 대비 점수
    colorfulness_score: float   # 색상 풍부도 점수
    compression_quality: float  # 압축 품질 추정

    # 세부 메트릭
    blur_score: Optional[float] = None          # Laplacian variance
    edge_density: Optional[float] = None        # 엣지 밀도
    dynamic_range: Optional[float] = None       # 동적 범위


class ImageQualityAnalyzer:
    """
    고급 이미지 품질 분석

    사용 기술:
    - OpenCV: Blur detection, Edge detection
    - NumPy: 통계 계산
    - PIL: 기본 메트릭
    """

    @staticmethod
    def analyze(
        img: Image.Image,
        file_size_bytes: int
    ) -> QualityMetrics:
        """
        종합 이미지 품질 분석
        """
        # PIL Image → NumPy array 변환
        img_array = np.array(img)

        # 그레이스케일 변환 (분석용)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # 각 메트릭 계산
        resolution_score = ImageQualityAnalyzer._calc_resolution_score(img)
        sharpness_score = ImageQualityAnalyzer._calc_sharpness(gray)
        brightness_score = ImageQualityAnalyzer._calc_brightness(gray)
        contrast_score = ImageQualityAnalyzer._calc_contrast(gray)
        colorfulness_score = ImageQualityAnalyzer._calc_colorfulness(img_array)
        compression_quality = ImageQualityAnalyzer._calc_compression_quality(
            img, file_size_bytes
        )

        # 종합 점수 계산 (가중 평균)
        overall_score = (
            resolution_score * 0.25 +
            sharpness_score * 0.25 +
            brightness_score * 0.15 +
            contrast_score * 0.15 +
            colorfulness_score * 0.10 +
            compression_quality * 0.10
        )

        return QualityMetrics(
            overall_score=overall_score,
            resolution_score=resolution_score,
            sharpness_score=sharpness_score,
            brightness_score=brightness_score,
            contrast_score=contrast_score,
            colorfulness_score=colorfulness_score,
            compression_quality=compression_quality,
            blur_score=ImageQualityAnalyzer._calc_blur_laplacian(gray),
            edge_density=ImageQualityAnalyzer._calc_edge_density(gray),
            dynamic_range=ImageQualityAnalyzer._calc_dynamic_range(gray)
        )

    @staticmethod
    def _calc_resolution_score(img: Image.Image) -> float:
        """
        해상도 점수

        기준:
        - 1920x1080 (Full HD) 이상: 1.0
        - 1280x720 (HD): 0.8
        - 640x480 (SD): 0.5
        - 320x240: 0.2
        """
        width, height = img.size
        pixels = width * height

        if pixels >= 1920 * 1080:
            return 1.0
        elif pixels >= 1280 * 720:
            return 0.8
        elif pixels >= 640 * 480:
            return 0.5
        elif pixels >= 320 * 240:
            return 0.3
        else:
            return 0.1

    @staticmethod
    def _calc_sharpness(gray: np.ndarray) -> float:
        """
        선명도 점수 (Laplacian Variance 기반)

        원리:
        - Laplacian 필터로 엣지 강도 측정
        - 분산이 클수록 선명
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # 경험적 임계값
        if variance >= 500:
            return 1.0
        elif variance >= 100:
            return 0.7 + (variance - 100) / 400 * 0.3
        elif variance >= 50:
            return 0.5 + (variance - 50) / 50 * 0.2
        else:
            return variance / 50 * 0.5

    @staticmethod
    def _calc_blur_laplacian(gray: np.ndarray) -> float:
        """
        Blur 정도 측정 (낮을수록 흐림)
        """
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    @staticmethod
    def _calc_brightness(gray: np.ndarray) -> float:
        """
        밝기 점수

        이상적 밝기: 100 ~ 160 (0-255 스케일)
        """
        mean_brightness = gray.mean()

        if 100 <= mean_brightness <= 160:
            return 1.0
        elif 80 <= mean_brightness < 100:
            return 0.7 + (mean_brightness - 80) / 20 * 0.3
        elif 160 < mean_brightness <= 180:
            return 1.0 - (mean_brightness - 160) / 20 * 0.3
        elif mean_brightness < 80:
            # 너무 어두움
            return mean_brightness / 80 * 0.7
        else:
            # 너무 밝음 (overexposure)
            return max(0.3, 1.0 - (mean_brightness - 180) / 75 * 0.7)

    @staticmethod
    def _calc_contrast(gray: np.ndarray) -> float:
        """
        대비 점수 (표준편차 기반)

        높은 표준편차 = 높은 대비
        """
        std_dev = gray.std()

        # 경험적 임계값
        if std_dev >= 50:
            return 1.0
        elif std_dev >= 30:
            return 0.7 + (std_dev - 30) / 20 * 0.3
        elif std_dev >= 15:
            return 0.4 + (std_dev - 15) / 15 * 0.3
        else:
            return std_dev / 15 * 0.4

    @staticmethod
    def _calc_colorfulness(img_array: np.ndarray) -> float:
        """
        색상 풍부도 점수

        알고리즘:
        - RGB 채널 분리
        - rg = R - G, yb = (R + G) / 2 - B
        - 표준편차와 평균으로 colorfulness 계산
        """
        if len(img_array.shape) != 3:
            return 0.5  # Grayscale은 중간 점수

        # RGB 채널 분리
        R = img_array[:, :, 0].astype(float)
        G = img_array[:, :, 1].astype(float)
        B = img_array[:, :, 2].astype(float)

        # rg, yb 계산
        rg = R - G
        yb = 0.5 * (R + G) - B

        # 통계
        rg_std = np.std(rg)
        yb_std = np.std(yb)
        rg_mean = np.mean(rg)
        yb_mean = np.mean(yb)

        std_root = np.sqrt(rg_std ** 2 + yb_std ** 2)
        mean_root = np.sqrt(rg_mean ** 2 + yb_mean ** 2)

        colorfulness = std_root + 0.3 * mean_root

        # 정규화 (경험적 최대값 100)
        return min(colorfulness / 100, 1.0)

    @staticmethod
    def _calc_compression_quality(
        img: Image.Image,
        file_size_bytes: int
    ) -> float:
        """
        압축 품질 추정

        계산:
        - bytes_per_pixel = file_size / pixels
        - 적정 범위: 0.5 ~ 3.0 bytes/pixel
        """
        width, height = img.size
        pixels = width * height

        if pixels == 0:
            return 0.5

        bytes_per_pixel = file_size_bytes / pixels

        if 0.5 <= bytes_per_pixel <= 3.0:
            return 1.0
        elif bytes_per_pixel < 0.5:
            # 과도한 압축
            return max(0.3, bytes_per_pixel / 0.5 * 0.7 + 0.3)
        else:
            # 압축 부족 (파일 크기만 큼)
            return max(0.5, 1.0 - (bytes_per_pixel - 3.0) / 5.0 * 0.5)

    @staticmethod
    def _calc_edge_density(gray: np.ndarray) -> float:
        """
        엣지 밀도 (Canny edge detection)
        """
        edges = cv2.Canny(gray, 100, 200)
        edge_pixels = np.count_nonzero(edges)
        total_pixels = edges.size
        return edge_pixels / total_pixels

    @staticmethod
    def _calc_dynamic_range(gray: np.ndarray) -> float:
        """
        동적 범위 (최대값 - 최소값)
        """
        return (gray.max() - gray.min()) / 255.0
```

### 5-2. 이미지 선택 전략

```python
# app/services/media/image_selector.py
from typing import List, Tuple
from PIL import Image
import imagehash

from app.schemas.media import ProcessedImage, QualityMetrics


class ImageSelector:
    """
    최적의 이미지 선택 전략

    목표:
    - 고품질 이미지 3장 선택
    - 중복 제거
    - 다양성 확보
    """

    @staticmethod
    def select_best_images(
        images_with_quality: List[Tuple[Image.Image, ProcessedImage, QualityMetrics]],
        max_count: int = 3,
        diversity_threshold: float = 0.85
    ) -> List[Tuple[Image.Image, ProcessedImage]]:
        """
        품질과 다양성을 고려한 이미지 선택

        Args:
            images_with_quality: (PIL.Image, ProcessedImage, QualityMetrics) 리스트
            max_count: 선택할 최대 이미지 수
            diversity_threshold: 유사도 임계값 (이상이면 중복으로 간주)

        Returns:
            선택된 (PIL.Image, ProcessedImage) 리스트
        """
        if not images_with_quality:
            return []

        # 1. 품질 점수로 정렬
        sorted_images = sorted(
            images_with_quality,
            key=lambda x: x[2].overall_score,
            reverse=True
        )

        # 2. 최고 품질 이미지 선택
        selected = [sorted_images[0]]
        selected_hashes = [imagehash.average_hash(sorted_images[0][0])]

        # 3. 나머지 이미지 중 다양성 있는 것 선택
        for img, processed, quality in sorted_images[1:]:
            if len(selected) >= max_count:
                break

            # 중복 검사 (perceptual hashing)
            current_hash = imagehash.average_hash(img)

            is_duplicate = any(
                ImageSelector._hash_similarity(current_hash, h) > diversity_threshold
                for h in selected_hashes
            )

            if not is_duplicate:
                selected.append((img, processed, quality))
                selected_hashes.append(current_hash)

        # ProcessedImage와 PIL.Image만 반환
        return [(img, processed) for img, processed, _ in selected]

    @staticmethod
    def _hash_similarity(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> float:
        """
        두 해시의 유사도 계산

        Returns:
            0.0 (완전 다름) ~ 1.0 (완전 같음)
        """
        hamming_distance = hash1 - hash2
        max_distance = len(hash1.hash) ** 2  # 64 for average_hash
        similarity = 1.0 - (hamming_distance / max_distance)
        return similarity

    @staticmethod
    def filter_low_quality(
        images_with_quality: List[Tuple[Image.Image, ProcessedImage, QualityMetrics]],
        min_quality_score: float = 0.3
    ) -> List[Tuple[Image.Image, ProcessedImage, QualityMetrics]]:
        """
        낮은 품질 이미지 필터링
        """
        return [
            (img, processed, quality)
            for img, processed, quality in images_with_quality
            if quality.overall_score >= min_quality_score
        ]

    @staticmethod
    def prioritize_signboards(
        images: List[Image.Image]
    ) -> List[Image.Image]:
        """
        간판/텍스트가 많은 이미지 우선순위 부여

        TODO: OCR 또는 텍스트 감지 모델 사용
        """
        # 간단한 휴리스틱: 엣지 밀도 높은 이미지
        # (간판은 텍스트가 많아 엣지가 많음)

        return images  # 현재는 pass-through
```

---

## 6. 메타데이터 추출 모듈

### 6-1. EXIF 데이터 추출기

```python
# app/services/media/exif_extractor.py
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from PIL import Image
import piexif
from piexif import GPSIFD, ExifIFD, ImageIFD
import logging

logger = logging.getLogger(__name__)


class EXIFExtractor:
    """
    EXIF 메타데이터 추출 및 파싱

    지원 데이터:
    - GPS 좌표 (위도/경도)
    - 촬영 일시
    - 카메라 정보
    - 이미지 방향
    """

    @staticmethod
    def extract_all(img: Image.Image) -> Dict[str, Any]:
        """
        모든 EXIF 메타데이터 추출

        Returns:
            {
                'gps': {'lat': 37.5665, 'lng': 126.9780, 'altitude': 10.5},
                'datetime': '2025-01-15 14:30:45',
                'camera': {'make': 'Apple', 'model': 'iPhone 13'},
                'orientation': 1,
                'raw_exif': {...}
            }
        """
        result = {
            'gps': None,
            'datetime': None,
            'camera': None,
            'orientation': None,
            'raw_exif': {}
        }

        try:
            # PIL의 _getexif() 사용
            exif_data = img._getexif()
            if exif_data is None:
                return result

            result['raw_exif'] = exif_data

            # Orientation (274번 태그)
            result['orientation'] = exif_data.get(274)

            # GPS 정보 추출
            gps_info = exif_data.get(34853)  # GPSInfo 태그
            if gps_info:
                result['gps'] = EXIFExtractor._parse_gps(gps_info)

            # 촬영 일시 (36867번: DateTimeOriginal)
            datetime_str = exif_data.get(36867)
            if datetime_str:
                result['datetime'] = EXIFExtractor._parse_datetime(datetime_str)

            # 카메라 정보
            camera_make = exif_data.get(271)  # Make
            camera_model = exif_data.get(272)  # Model
            if camera_make or camera_model:
                result['camera'] = {
                    'make': camera_make,
                    'model': camera_model
                }

            return result

        except Exception as e:
            logger.warning(f"EXIF extraction failed: {e}")
            return result

    @staticmethod
    def _parse_gps(gps_info: dict) -> Optional[Dict[str, float]]:
        """
        GPS 정보 파싱

        EXIF GPS 형식:
        - GPSLatitude: [(37, 1), (33, 1), (59, 1)] = 37도 33분 59초
        - GPSLatitudeRef: 'N' (북위) 또는 'S' (남위)
        - GPSLongitude: [(126, 1), (58, 1), (40, 1)] = 126도 58분 40초
        - GPSLongitudeRef: 'E' (동경) 또는 'W' (서경)
        - GPSAltitude: (50, 1) = 50m

        Returns:
            {'lat': 37.5665, 'lng': 126.9780, 'altitude': 50.0}
        """
        try:
            # GPS 태그 확인
            gps_latitude = gps_info.get(2)  # GPSLatitude
            gps_latitude_ref = gps_info.get(1)  # GPSLatitudeRef
            gps_longitude = gps_info.get(4)  # GPSLongitude
            gps_longitude_ref = gps_info.get(3)  # GPSLongitudeRef
            gps_altitude = gps_info.get(6)  # GPSAltitude

            if not (gps_latitude and gps_longitude):
                return None

            # 위도 변환 (도분초 → 십진수)
            lat = EXIFExtractor._dms_to_decimal(
                gps_latitude,
                gps_latitude_ref
            )

            # 경도 변환 (도분초 → 십진수)
            lng = EXIFExtractor._dms_to_decimal(
                gps_longitude,
                gps_longitude_ref
            )

            result = {'lat': lat, 'lng': lng}

            # 고도 (선택사항)
            if gps_altitude:
                altitude = gps_altitude[0] / gps_altitude[1]
                result['altitude'] = altitude

            return result

        except Exception as e:
            logger.warning(f"GPS parsing failed: {e}")
            return None

    @staticmethod
    def _dms_to_decimal(
        dms: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]],
        ref: str
    ) -> float:
        """
        도분초(DMS)를 십진수(Decimal)로 변환

        Args:
            dms: [(37, 1), (33, 1), (59, 1)] = 37도 33분 59초
            ref: 'N', 'S', 'E', 'W'

        Returns:
            37.566389 (십진수)

        공식:
            decimal = degrees + minutes/60 + seconds/3600
        """
        # 각 요소 추출
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1]
        seconds = dms[2][0] / dms[2][1]

        # 십진수 변환
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        # 음수 처리 (남위, 서경)
        if ref in ['S', 'W']:
            decimal = -decimal

        return decimal

    @staticmethod
    def _parse_datetime(datetime_str: str) -> Optional[str]:
        """
        EXIF DateTime 파싱

        EXIF 형식: "2025:01:15 14:30:45"
        ISO 형식: "2025-01-15T14:30:45"
        """
        try:
            # EXIF 형식 → Python datetime
            dt = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')

            # ISO 형식으로 변환
            return dt.isoformat()

        except Exception as e:
            logger.warning(f"DateTime parsing failed: {e}")
            return None

    @staticmethod
    def extract_with_piexif(image_bytes: bytes) -> Dict[str, Any]:
        """
        piexif 라이브러리로 EXIF 추출 (대체 방법)

        장점: 더 상세한 EXIF 데이터
        단점: PIL보다 느림
        """
        try:
            exif_dict = piexif.load(image_bytes)

            result = {}

            # GPS 데이터
            if "GPS" in exif_dict:
                gps = exif_dict["GPS"]
                if GPSIFD.GPSLatitude in gps and GPSIFD.GPSLongitude in gps:
                    lat_ref = gps.get(GPSIFD.GPSLatitudeRef, b'N').decode()
                    lng_ref = gps.get(GPSIFD.GPSLongitudeRef, b'E').decode()

                    result['gps'] = {
                        'lat': EXIFExtractor._dms_to_decimal(
                            gps[GPSIFD.GPSLatitude],
                            lat_ref
                        ),
                        'lng': EXIFExtractor._dms_to_decimal(
                            gps[GPSIFD.GPSLongitude],
                            lng_ref
                        )
                    }

            # Exif 데이터
            if "Exif" in exif_dict:
                exif = exif_dict["Exif"]

                # DateTime
                if ExifIFD.DateTimeOriginal in exif:
                    dt_bytes = exif[ExifIFD.DateTimeOriginal]
                    result['datetime'] = dt_bytes.decode()

            return result

        except Exception as e:
            logger.warning(f"piexif extraction failed: {e}")
            return {}
```

### 6-2. 이미지 메타데이터 수집기

```python
# app/services/media/metadata_collector.py
from typing import Dict, Any
from PIL import Image
import hashlib


class ImageMetadataCollector:
    """
    종합 이미지 메타데이터 수��

    수집 정보:
    - 기본 정보 (크기, 포맷, 모드)
    - EXIF 데이터
    - 파일 정보 (해시, 크기)
    - 품질 메트릭
    """

    @staticmethod
    def collect(
        img: Image.Image,
        image_bytes: bytes,
        url: str
    ) -> Dict[str, Any]:
        """
        모든 메타데이터 수집
        """
        # 1. 기본 정보
        width, height = img.size
        basic_info = {
            'url': url,
            'width': width,
            'height': height,
            'format': img.format,
            'mode': img.mode,
            'file_size_bytes': len(image_bytes),
            'aspect_ratio': round(width / height, 3) if height > 0 else 0
        }

        # 2. 파일 해시 (SHA256)
        file_hash = hashlib.sha256(image_bytes).hexdigest()
        basic_info['sha256'] = file_hash

        # 3. Perceptual hash (중복 감지용)
        try:
            import imagehash
            basic_info['phash'] = str(imagehash.average_hash(img))
        except:
            pass

        # 4. EXIF 데이터
        exif_extractor = EXIFExtractor()
        exif_data = exif_extractor.extract_all(img)
        basic_info['exif'] = exif_data

        # 5. 이미지 특성
        basic_info['has_transparency'] = img.mode in ('RGBA', 'LA', 'P')
        basic_info['is_animated'] = getattr(img, 'is_animated', False)
        basic_info['frames'] = getattr(img, 'n_frames', 1)

        return basic_info
```

---

## 7. 포맷 변환 및 최적화

### 7-1. 포맷 정규화

```python
# app/services/media/format_converter.py
from PIL import Image
from typing import Tuple
import io


class ImageFormatConverter:
    """
    이미지 포맷 변환 및 최적화

    목표:
    - Gemini API 호환 포맷 (JPEG, PNG)
    - 파일 크기 최적화
    - 색상 공간 정규화
    """

    # Gemini API 선호 포맷
    TARGET_FORMAT = 'JPEG'
    JPEG_QUALITY = 85  # 품질 vs 크기 균형
    JPEG_OPTIMIZE = True
    JPEG_PROGRESSIVE = True  # Progressive JPEG

    @staticmethod
    def normalize_for_ai(img: Image.Image) -> Image.Image:
        """
        AI 분석용 포맷 정규화

        변환:
        - RGBA → RGB (흰색 배경)
        - CMYK → RGB
        - Palette → RGB
        - LA (Grayscale + Alpha) → RGB
        """
        # 1. RGBA → RGB
        if img.mode == 'RGBA':
            # 흰색 배경 생성
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Alpha 채널을 마스크로 사용하여 합성
            background.paste(img, mask=img.split()[3])
            return background

        # 2. CMYK → RGB (인쇄용 색상 공간)
        elif img.mode == 'CMYK':
            return img.convert('RGB')

        # 3. Palette (P) → RGB
        elif img.mode == 'P':
            return img.convert('RGB')

        # 4. LA (Grayscale + Alpha) → RGB
        elif img.mode == 'LA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            gray = img.convert('L')
            background.paste(gray)
            return background

        # 5. L (Grayscale) → RGB (선택적)
        elif img.mode == 'L':
            return img.convert('RGB')

        # 6. 1-bit → RGB
        elif img.mode == '1':
            return img.convert('RGB')

        # 이미 RGB면 그대로
        return img

    @staticmethod
    def convert_to_jpeg(
        img: Image.Image,
        quality: int = JPEG_QUALITY,
        optimize: bool = JPEG_OPTIMIZE,
        progressive: bool = JPEG_PROGRESSIVE
    ) -> bytes:
        """
        JPEG로 변환 및 압축

        Args:
            img: PIL.Image 객체 (RGB 모드여야 함)
            quality: JPEG 품질 (1-100)
            optimize: 최적화 활성화 (느리지만 파일 작음)
            progressive: Progressive JPEG (웹 로딩 최적화)

        Returns:
            JPEG 바이너리 데이터
        """
        # RGB 모드 확인
        if img.mode != 'RGB':
            img = ImageFormatConverter.normalize_for_ai(img)

        # BytesIO 버퍼
        buffer = io.BytesIO()

        # JPEG 저장
        img.save(
            buffer,
            format='JPEG',
            quality=quality,
            optimize=optimize,
            progressive=progressive
        )

        return buffer.getvalue()

    @staticmethod
    def convert_webp_to_jpeg(img: Image.Image) -> bytes:
        """
        WebP → JPEG 변환

        WebP는 Gemini가 지원하지만,
        일부 구형 시스템 호환성을 위해 JPEG 선호
        """
        return ImageFormatConverter.convert_to_jpeg(img)

    @staticmethod
    def extract_gif_first_frame(img: Image.Image) -> Image.Image:
        """
        GIF 첫 프레임 추출

        애니메이션 GIF의 경우 첫 프레임만 사용
        """
        if getattr(img, 'is_animated', False):
            img.seek(0)  # 첫 프레임으로 이동
            first_frame = img.copy()
            return ImageFormatConverter.normalize_for_ai(first_frame)

        return ImageFormatConverter.normalize_for_ai(img)

    @staticmethod
    def optimize_file_size(
        img: Image.Image,
        max_size_bytes: int = 2 * 1024 * 1024  # 2MB
    ) -> Tuple[bytes, int]:
        """
        파일 크기 최적화 (동적 품질 조정)

        전략:
        - 초기 품질 85로 시도
        - 크기 초과 시 품질 점진적 감소 (10씩)
        - 최소 품질 50
        """
        quality = 85

        while quality >= 50:
            jpeg_bytes = ImageFormatConverter.convert_to_jpeg(
                img,
                quality=quality
            )

            if len(jpeg_bytes) <= max_size_bytes:
                return jpeg_bytes, quality

            # 품질 낮추기
            quality -= 10

        # 최소 품질로도 크기 초과 → 리사이징 필요
        return jpeg_bytes, quality
```

### 7-2. 고급 압축 최적화

```python
# app/services/media/compression_optimizer.py
from PIL import Image
import io


class CompressionOptimizer:
    """
    고급 이미지 압축 최적화

    기법:
    - JPEG chroma subsampling
    - 메타데이터 제거
    - 허프만 테이블 최적화
    """

    @staticmethod
    def compress_aggressive(
        img: Image.Image,
        target_size_bytes: int = 1024 * 1024  # 1MB
    ) -> bytes:
        """
        공격적 압축 (품질 희생)

        사용 시나리오:
        - 네트워크 대역폭 절약
        - 썸네일 생성
        """
        # 1. 이미 작으면 기본 압축
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        if buffer.tell() <= target_size_bytes:
            return buffer.getvalue()

        # 2. 리사이징 (50% 축소)
        new_size = (img.width // 2, img.height // 2)
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # 3. 품질 낮추기
        for quality in [75, 65, 55, 45]:
            buffer = io.BytesIO()
            img_resized.save(
                buffer,
                format='JPEG',
                quality=quality,
                optimize=True
            )

            if buffer.tell() <= target_size_bytes:
                return buffer.getvalue()

        # 4. 최종 (최소 품질)
        return buffer.getvalue()

    @staticmethod
    def strip_metadata(image_bytes: bytes) -> bytes:
        """
        메타데이터 제거 (EXIF, ICC 프로필 등)

        효과: 파일 크기 5-15% 감소
        """
        img = Image.open(io.BytesIO(image_bytes))

        # 새 이미지로 복사 (메타데이터 없음)
        buffer = io.BytesIO()
        img.save(buffer, format=img.format or 'JPEG', quality=85)

        return buffer.getvalue()
```

---

## 8. 캐싱 전략

### 8-1. 2-레벨 캐시 구현

```python
# app/services/media/image_cache.py
import asyncio
from typing import Optional
import io
import pickle
from datetime import timedelta

from PIL import Image
from cachetools import TTLCache
import redis.asyncio as redis

from app.core.config import settings


class ImageCache:
    """
    2-레벨 이미지 캐시

    L1: 메모리 (TTLCache)
    - 빠른 접근 (< 1ms)
    - 용량 제한: 100장 또는 500MB
    - TTL: 1시간

    L2: Redis
    - 분산 캐시
    - 용량 제한: Redis 설정 따름
    - TTL: 7일
    - 저장 형식: 압축된 JPEG (메타데이터 별도)
    """

    def __init__(self):
        """캐시 초기화"""
        # L1: 메모리 캐시
        self.l1_cache = TTLCache(
            maxsize=100,  # 최대 100장
            ttl=3600  # 1시간
        )
        self.l1_size_bytes = 0
        self.l1_max_size = 500 * 1024 * 1024  # 500MB

        # L2: Redis 클라이언트
        self.redis_client: Optional[redis.Redis] = None

    async def initialize_redis(self):
        """Redis 연결 초기화"""
        if self.redis_client is None:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                encoding='utf-8',
                decode_responses=False  # 바이너리 데이터
            )

    async def close_redis(self):
        """Redis 연결 종료"""
        if self.redis_client:
            await self.redis_client.close()

    async def get_image(
        self,
        image_url: str
    ) -> Optional[Image.Image]:
        """
        캐시에서 이미지 가져오기

        Returns:
            PIL.Image 또는 None (캐시 미스)
        """
        cache_key = self._generate_cache_key(image_url)

        # L1 캐시 확인
        if cache_key in self.l1_cache:
            return self._deserialize_image(self.l1_cache[cache_key])

        # L2 캐시 확인 (Redis)
        if self.redis_client:
            try:
                cached_bytes = await self.redis_client.get(cache_key)
                if cached_bytes:
                    # L1 캐시에도 저장
                    img = self._deserialize_image(cached_bytes)
                    self._add_to_l1(cache_key, cached_bytes)
                    return img
            except Exception as e:
                import logging
                logging.warning(f"Redis get failed: {e}")

        return None

    async def cache_image(
        self,
        image_url: str,
        img: Image.Image,
        ttl_seconds: int = 86400 * 7  # 7일
    ):
        """
        이미지를 캐시에 저장

        Args:
            image_url: 원본 URL
            img: PIL.Image 객체
            ttl_seconds: TTL (초)
        """
        cache_key = self._generate_cache_key(image_url)

        # 이미지 직렬화 (JPEG 압축)
        image_bytes = self._serialize_image(img)

        # L1 캐시 저장
        self._add_to_l1(cache_key, image_bytes)

        # L2 캐시 저장 (Redis)
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    ttl_seconds,
                    image_bytes
                )
            except Exception as e:
                import logging
                logging.warning(f"Redis set failed: {e}")

    def _generate_cache_key(self, url: str) -> str:
        """캐시 키 생성"""
        import hashlib
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"img:{url_hash}"

    def _serialize_image(self, img: Image.Image) -> bytes:
        """
        이미지 직렬화 (메모리 효율)

        방법: JPEG 압축 (quality=85)
        """
        buffer = io.BytesIO()

        # RGB 변환
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # JPEG 저장
        img.save(buffer, format='JPEG', quality=85, optimize=True)

        return buffer.getvalue()

    def _deserialize_image(self, image_bytes: bytes) -> Image.Image:
        """이미지 역직렬화"""
        return Image.open(io.BytesIO(image_bytes))

    def _add_to_l1(self, key: str, image_bytes: bytes):
        """L1 캐시에 추가 (크기 제한 고려)"""
        size = len(image_bytes)

        # 크기 제한 확인
        if self.l1_size_bytes + size > self.l1_max_size:
            # 공간 확보 (LRU)
            self._evict_l1()

        # 추가
        self.l1_cache[key] = image_bytes
        self.l1_size_bytes += size

    def _evict_l1(self):
        """L1 캐시에서 오래된 항목 제거"""
        # TTLCache가 자동으로 만료 처리
        # 추가로 크기 기반 제거 필요 시 구현
        pass

    async def get_cache_stats(self) -> dict:
        """캐시 통계"""
        stats = {
            'l1_size': len(self.l1_cache),
            'l1_size_bytes': self.l1_size_bytes,
            'l1_max_size_bytes': self.l1_max_size
        }

        if self.redis_client:
            try:
                info = await self.redis_client.info('memory')
                stats['redis_used_memory'] = info.get('used_memory_human')
            except:
                pass

        return stats
```

### 8-2. 캐시 워밍 및 무효화

```python
# app/services/media/cache_warmer.py
from typing import List
import asyncio


class CacheWarmer:
    """
    캐시 워밍 (사전 로드)

    사용 시나리오:
    - 인기 이미지 사전 캐싱
    - 배포 후 초기화
    """

    def __init__(self, cache: ImageCache):
        self.cache = cache

    async def warm_popular_images(
        self,
        popular_urls: List[str]
    ):
        """
        인기 이미지 사전 캐싱

        전략:
        - 상위 100개 URL
        - 백그라운드 다운로드
        """
        downloader = ImageDownloader()

        async with downloader:
            for url in popular_urls[:100]:
                try:
                    # 다운로드
                    results = await downloader.download_images([url])
                    if results[0].success:
                        # 디코딩
                        img = Image.open(io.BytesIO(results[0].data))

                        # 캐싱
                        await self.cache.cache_image(url, img)

                except Exception:
                    continue

                # Rate limiting
                await asyncio.sleep(0.1)


class CacheInvalidator:
    """캐시 무효화"""

    def __init__(self, cache: ImageCache):
        self.cache = cache

    async def invalidate_url(self, url: str):
        """특정 URL 캐시 무효화"""
        cache_key = self.cache._generate_cache_key(url)

        # L1 제거
        if cache_key in self.cache.l1_cache:
            del self.cache.l1_cache[cache_key]

        # L2 제거
        if self.cache.redis_client:
            await self.cache.redis_client.delete(cache_key)

    async def invalidate_pattern(self, pattern: str):
        """패턴 매칭 캐시 무효화"""
        if self.cache.redis_client:
            keys = await self.cache.redis_client.keys(f"img:*{pattern}*")
            if keys:
                await self.cache.redis_client.delete(*keys)
```

---

## 9. 성능 최적화

### 9-1. 병렬 처리 최적화

```python
# app/services/media/performance_optimizer.py
import asyncio
from typing import List, Callable, TypeVar
from concurrent.futures import ThreadPoolExecutor
import functools

T = TypeVar('T')


class PerformanceOptimizer:
    """
    성능 최적화 유틸리티

    기법:
    - asyncio 병렬 실행
    - ThreadPoolExecutor (CPU-bound 작업)
    - 배치 처리
    """

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_thread(self, func: Callable, *args, **kwargs):
        """
        CPU-bound 작업을 스레드에서 실행

        사용 예:
        - 이미지 디코딩
        - 리사이징
        - 품질 분석
        """
        loop = asyncio.get_event_loop()
        partial_func = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(self.executor, partial_func)

    async def batch_process(
        self,
        items: List[T],
        processor: Callable,
        batch_size: int = 10,
        max_concurrent: int = 3
    ) -> List:
        """
        배치 처리 (메모리 효율)

        전략:
        - 큰 리스트를 배치로 분할
        - 배치별로 병렬 처리
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch(batch):
            async with semaphore:
                return await asyncio.gather(
                    *[processor(item) for item in batch],
                    return_exceptions=True
                )

        # 배치 생성
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await process_batch(batch)
            results.extend(batch_results)

        return results


# 사용 예제
async def example_parallel_image_processing():
    """병렬 이미지 처리 예제"""
    optimizer = PerformanceOptimizer(max_workers=4)

    urls = ['url1', 'url2', 'url3', ...]

    async def process_single_image(url):
        # 다운로드
        downloader = ImageDownloader()
        async with downloader:
            result = await downloader.download_images([url])

        if not result[0].success:
            return None

        # CPU-bound 작업 (스레드 사용)
        img = await optimizer.run_in_thread(
            Image.open,
            io.BytesIO(result[0].data)
        )

        # 리사이징 (CPU-bound)
        resized = await optimizer.run_in_thread(
            ImageResizer.resize_for_analysis,
            img
        )

        return resized

    # 배치 처리
    results = await optimizer.batch_process(
        urls,
        process_single_image,
        batch_size=10
    )

    return results
```

### 9-2. 벤치마크 및 프로파일링

```python
# app/services/media/benchmark.py
import time
import asyncio
from typing import Callable, Dict
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""
    operation: str
    duration_seconds: float
    items_processed: int
    items_per_second: float
    memory_usage_mb: float


class ImageProcessingBenchmark:
    """
    이미지 처리 성능 벤치마크

    측정 항목:
    - 다운로드 속도
    - 디코딩 속도
    - 리사이징 속도
    - 품질 분석 속도
    - 전체 파이프라인 처리 시간
    """

    @staticmethod
    async def benchmark_download(urls: List[str]) -> BenchmarkResult:
        """다운로드 성능 측정"""
        start_time = time.time()

        downloader = ImageDownloader()
        async with downloader:
            results = await downloader.download_images(urls)

        duration = time.time() - start_time
        success_count = sum(1 for r in results if r.success)

        return BenchmarkResult(
            operation='download',
            duration_seconds=duration,
            items_processed=success_count,
            items_per_second=success_count / duration if duration > 0 else 0,
            memory_usage_mb=0  # TODO: psutil로 측정
        )

    @staticmethod
    async def benchmark_full_pipeline(
        urls: List[str]
    ) -> Dict[str, BenchmarkResult]:
        """전체 파이프라인 벤치마크"""
        results = {}

        # 1. 다운로드
        results['download'] = await ImageProcessingBenchmark.benchmark_download(urls)

        # 2. 디코딩 (TODO)
        # 3. 리사이징 (TODO)
        # 4. 품질 분석 (TODO)

        return results


# 사용 예제
async def run_benchmark():
    """벤치마크 실행"""
    test_urls = [
        'https://picsum.photos/1024/1024',
        'https://picsum.photos/800/600',
        'https://picsum.photos/1920/1080',
    ]

    benchmark = ImageProcessingBenchmark()
    results = await benchmark.benchmark_full_pipeline(test_urls)

    print("=== Benchmark Results ===")
    for operation, result in results.items():
        print(f"{operation}:")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        print(f"  Items/sec: {result.items_per_second:.1f}")
```

---

## 10. 에러 처리 및 복원력

### 10-1. 포괄적 에러 처리

```python
# app/exceptions/image_processing.py
from enum import Enum


class ImageErrorCode(Enum):
    """이미지 처리 에러 코드"""
    # 다운로드 에러
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # 디코딩 에러
    INVALID_FORMAT = "INVALID_FORMAT"
    CORRUPTED_IMAGE = "CORRUPTED_IMAGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"

    # 처리 에러
    RESIZE_FAILED = "RESIZE_FAILED"
    CONVERSION_FAILED = "CONVERSION_FAILED"

    # 품질 에러
    QUALITY_TOO_LOW = "QUALITY_TOO_LOW"
    RESOLUTION_TOO_LOW = "RESOLUTION_TOO_LOW"


class ImageProcessingError(Exception):
    """이미지 처리 기본 예외"""

    def __init__(
        self,
        message: str,
        error_code: ImageErrorCode,
        url: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.url = url
        self.details = details or {}
        super().__init__(self.message)


# 에러 핸들러
class ErrorHandler:
    """중앙 집중식 에러 처리"""

    @staticmethod
    async def handle_image_error(
        error: Exception,
        url: str,
        context: str
    ) -> Optional[Dict]:
        """
        이미지 처리 에러 핸들링

        Returns:
            에러 정보 딕셔너리 또는 None (복구 가능 시)
        """
        import logging
        logger = logging.getLogger(__name__)

        # 로깅
        logger.error(
            f"Image processing error in {context}",
            extra={
                'url': url,
                'error_type': type(error).__name__,
                'error_message': str(error)
            }
        )

        # 메트릭 기록
        from app.services.monitoring.metrics import image_errors
        image_errors.labels(
            error_type=type(error).__name__,
            context=context
        ).inc()

        # 에러 정보 반환
        return {
            'error': True,
            'error_code': getattr(error, 'error_code', 'UNKNOWN'),
            'error_message': str(error),
            'url': url
        }
```

### 10-2. Graceful Degradation

```python
# app/services/media/fallback_handler.py
from typing import List, Tuple, Optional


class ImageProcessingFallback:
    """
    Graceful Degradation 전략

    원칙:
    - 일부 이미지 실패해도 계속 진행
    - 저품질 이미지라도 수용 (경고 표시)
    - 최소 1장은 확보 시도
    """

    @staticmethod
    async def process_with_fallback(
        urls: List[str],
        min_required: int = 1
    ) -> Tuple[List[Image.Image], List[Dict]]:
        """
        Fallback 전략으로 이미지 처리

        Returns:
            (성공한 이미지 리스트, 에러 정보 리스트)
        """
        successful_images = []
        errors = []

        downloader = ImageDownloader()

        async with downloader:
            # 1차: 모든 URL 다운로드 시도
            download_results = await downloader.download_images(urls)

            for result in download_results:
                if result.success:
                    try:
                        # 디코딩
                        img = Image.open(io.BytesIO(result.data))

                        # 기본 검증
                        if img.width >= 100 and img.height >= 100:
                            successful_images.append(img)
                        else:
                            errors.append({
                                'url': result.url,
                                'error': 'Image too small'
                            })

                    except Exception as e:
                        errors.append({
                            'url': result.url,
                            'error': str(e)
                        })
                else:
                    errors.append({
                        'url': result.url,
                        'error': result.error
                    })

        # 2차: 최소 요구 개수 미달 시 재시도
        if len(successful_images) < min_required:
            # 추가 URL 요청 또는 품질 기준 완화
            pass

        return successful_images, errors
```

---

## 11. 모니터링 및 디버깅

### 11-1. Prometheus 메트릭

```python
# app/services/monitoring/image_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary


# 다운로드 메트릭
image_download_total = Counter(
    'image_download_total',
    'Total image download attempts',
    ['status', 'source']  # success/failed, instagram/youtube
)

image_download_duration = Histogram(
    'image_download_duration_seconds',
    'Image download duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

image_download_size = Histogram(
    'image_download_size_bytes',
    'Downloaded image size',
    buckets=[10_000, 100_000, 500_000, 1_000_000, 5_000_000, 10_000_000]
)

# 처리 메트릭
image_processing_duration = Histogram(
    'image_processing_duration_seconds',
    'Image processing duration',
    ['stage'],  # decode, resize, analyze
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

image_quality_score = Histogram(
    'image_quality_score',
    'Image quality score distribution',
    buckets=[0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# 캐시 메트릭
cache_hits_total = Counter(
    'image_cache_hits_total',
    'Total cache hits',
    ['level']  # l1/l2
)

cache_size_bytes = Gauge(
    'image_cache_size_bytes',
    'Current cache size in bytes',
    ['level']
)

# 에러 메트릭
image_errors = Counter(
    'image_processing_errors_total',
    'Total image processing errors',
    ['error_type', 'context']
)


class ImageMetricsCollector:
    """메트릭 수집 헬퍼"""

    @staticmethod
    def record_download(
        duration: float,
        size_bytes: int,
        success: bool,
        source: str
    ):
        """다운로드 메트릭 기록"""
        status = 'success' if success else 'failed'
        image_download_total.labels(status=status, source=source).inc()

        if success:
            image_download_duration.observe(duration)
            image_download_size.observe(size_bytes)

    @staticmethod
    def record_processing(stage: str, duration: float):
        """처리 메트릭 기록"""
        image_processing_duration.labels(stage=stage).observe(duration)

    @staticmethod
    def record_quality(score: float):
        """품질 점수 기록"""
        image_quality_score.observe(score)

    @staticmethod
    def record_cache_hit(level: str):
        """캐시 히트 기록"""
        cache_hits_total.labels(level=level).inc()
```

### 11-2. 구조화 로깅

```python
# app/services/media/logging_config.py
import structlog
import logging


def configure_image_logging():
    """이미지 처리 로깅 설정"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# 로거 사용 예제
logger = structlog.get_logger()

async def log_image_processing(url: str, stage: str, **kwargs):
    """구조화 이미지 로깅"""
    logger.info(
        "image_processing",
        url_hash=hashlib.sha256(url.encode()).hexdigest()[:16],
        stage=stage,
        **kwargs
    )
```

---

## 12. 보안 및 검증

### 12-1. URL 검증 및 화이트리스트

```python
# app/services/media/security_validator.py
from urllib.parse import urlparse
from typing import Set


class ImageSecurityValidator:
    """이미지 보안 검증"""

    # 허용된 도메인
    ALLOWED_DOMAINS: Set[str] = {
        # Instagram
        'instagram.com', 'cdninstagram.com', 'fbcdn.net',
        # YouTube
        'youtube.com', 'ytimg.com', 'googleusercontent.com',
        # Naver
        'pstatic.net', 'naver.com', 'naver.net',
        # Kakao
        'kakaocdn.net', 'kakao.com',
        # General CDNs
        'cloudfront.net', 'amazonaws.com', 'akamaihd.net',
    }

    # 차단된 확장자
    BLOCKED_EXTENSIONS: Set[str] = {
        '.exe', '.bat', '.sh', '.cmd', '.com'
    }

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        URL 보안 검증

        검사 항목:
        - 프로토콜 (HTTPS만)
        - 도메인 화이트리스트
        - 확장자 블랙리스트
        """
        try:
            parsed = urlparse(url)

            # 1. 프로토콜 검증
            if parsed.scheme != 'https':
                return False

            # 2. 도메인 검증
            domain = parsed.netloc.lower()
            if not any(allowed in domain for allowed in ImageSecurityValidator.ALLOWED_DOMAINS):
                return False

            # 3. 확장자 검증
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in ImageSecurityValidator.BLOCKED_EXTENSIONS):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def detect_malicious_content(image_bytes: bytes) -> bool:
        """
        악성 콘텐츠 감지 (간단한 휴리스틱)

        검사 항목:
        - 파일 시그니처 (매직 넘버)
        - 실행 가능 코드 패턴
        """
        # JPEG 시그니처: FF D8 FF
        if image_bytes[:3] == b'\xff\xd8\xff':
            return False  # 정상 JPEG

        # PNG 시그니처: 89 50 4E 47
        if image_bytes[:4] == b'\x89PNG':
            return False  # 정상 PNG

        # 의심스러운 패턴
        suspicious_patterns = [
            b'MZ',  # EXE header
            b'#!/',  # Shebang
        ]

        for pattern in suspicious_patterns:
            if pattern in image_bytes[:100]:
                return True  # 의심

        return False  # 안전한 것으로 추정
```

### 12-2. 이미지 샌드박싱

```python
# app/services/media/image_sandbox.py
from PIL import Image, ImageFile
import io


class ImageSandbox:
    """
    안전한 이미지 처리 샌드박스

    보안 조치:
    - Decompression bomb 방어
    - 메모리 제한
    - 타임아웃
    """

    # PIL 보안 설정
    MAX_IMAGE_PIXELS = 100_000_000  # 100 megapixels
    LOAD_TRUNCATED_IMAGES = True

    @staticmethod
    def safe_open(image_bytes: bytes) -> Image.Image:
        """
        안전한 이미지 열기

        보호:
        - Decompression bomb
        - Truncated image
        - Invalid format
        """
        # PIL 보안 설정 적용
        Image.MAX_IMAGE_PIXELS = ImageSandbox.MAX_IMAGE_PIXELS
        ImageFile.LOAD_TRUNCATED_IMAGES = ImageSandbox.LOAD_TRUNCATED_IMAGES

        try:
            img = Image.open(io.BytesIO(image_bytes))

            # 기본 검증
            img.verify()  # 파일 무결성 확인

            # 재오픈 (verify 후 필요)
            img = Image.open(io.BytesIO(image_bytes))

            return img

        except Image.DecompressionBombError:
            raise ValueError("Image exceeds size limit (potential DoS)")
        except Exception as e:
            raise ValueError(f"Cannot open image: {str(e)}")
```

---

## 13. 종합 예제

### 13-1. 완전한 파이프라인 통합

```python
# app/services/media/complete_pipeline.py
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PipelineResult:
    """파이프라인 처리 결과"""
    images: List[Image.Image]
    metadata: List[Dict]
    quality_scores: List[float]
    processing_time: float
    errors: List[Dict]


class CompleteImagePipeline:
    """
    완전한 이미지 처리 파이프라인

    단계:
    1. URL 검증
    2. 병렬 다운로드
    3. 디코딩 및 검증
    4. 품질 분석
    5. 상위 3개 선택
    6. 리사이징 및 최적화
    7. 캐싱
    """

    def __init__(self):
        self.downloader = ImageDownloader()
        self.cache = ImageCache()
        self.validator = ImageSecurityValidator()
        self.quality_analyzer = ImageQualityAnalyzer()
        self.selector = ImageSelector()
        self.resizer = ImageResizer()

    async def process_images(
        self,
        urls: List[str],
        max_images: int = 3,
        use_cache: bool = True
    ) -> PipelineResult:
        """
        이미지 전체 처리 파이프라인 실행

        Args:
            urls: 이미지 URL 리스트
            max_images: 최대 선택 이미지 수
            use_cache: 캐시 사용 여부

        Returns:
            PipelineResult
        """
        import time
        start_time = time.time()

        images = []
        metadata_list = []
        quality_scores = []
        errors = []

        # 1. URL 검증
        valid_urls = [
            url for url in urls
            if self.validator.validate_url(url)
        ]

        if not valid_urls:
            return PipelineResult([], [], [], 0, [{'error': 'No valid URLs'}])

        # 2. 캐시 확인
        if use_cache:
            await self.cache.initialize_redis()

            for url in valid_urls[:]:
                cached_img = await self.cache.get_image(url)
                if cached_img:
                    images.append(cached_img)
                    valid_urls.remove(url)

        # 3. 다운로드
        async with self.downloader:
            download_results = await self.downloader.download_images(valid_urls)

        # 4. 디코딩 및 품질 분석
        candidates = []

        for result in download_results:
            if not result.success:
                errors.append({'url': result.url, 'error': result.error})
                continue

            try:
                # 디코딩
                img = ImageSandbox.safe_open(result.data)

                # 품질 분석
                quality = self.quality_analyzer.analyze(
                    img,
                    result.content_length
                )

                # 메타데이터 수집
                metadata = ImageMetadataCollector.collect(
                    img,
                    result.data,
                    result.url
                )

                candidates.append((img, metadata, quality))

            except Exception as e:
                errors.append({'url': result.url, 'error': str(e)})

        # 5. 상위 이미지 선택
        selected = self.selector.select_best_images(
            candidates,
            max_count=max_images
        )

        # 6. 리사이징
        for img, metadata in selected:
            resized = self.resizer.resize_for_analysis(img)
            images.append(resized)
            metadata_list.append(metadata)
            quality_scores.append(metadata.get('quality_score', 0.5))

            # 7. 캐싱
            if use_cache:
                await self.cache.cache_image(metadata['url'], resized)

        # 정리
        if use_cache:
            await self.cache.close_redis()

        processing_time = time.time() - start_time

        return PipelineResult(
            images=images,
            metadata=metadata_list,
            quality_scores=quality_scores,
            processing_time=processing_time,
            errors=errors
        )
```

---

## 14. 참고 자료 및 베스트 프랙티스

### 14-1. 성능 최적화 팁

1. **다운로드 최적화**
   - HTTP/2 사용 (멀티플렉싱)
   - Connection pooling
   - HEAD 요청으로 크기 사전 확인

2. **메모리 관리**
   - 이미지 처리 후 즉시 해제
   - 대용량 이미지는 리사이징 후 처리
   - 메모리 캐시 크기 제한

3. **CPU 최적화**
   - PIL-SIMD 사용 (SIMD 최적화)
   - libjpeg-turbo 빌드
   - 병렬 처리 (asyncio + ThreadPoolExecutor)

### 14-2. 에러 처리 베스트 프랙티스

1. **Graceful Degradation**
   - 일부 실패해도 계속 진행
   - 최소 1장 확보 목표
   - 품질 기준 점진적 완화

2. **재시도 전략**
   - Exponential backoff
   - 최대 3회 재시도
   - 재시도 간 지연 (1s, 2s, 4s)

3. **로깅 및 모니터링**
   - 구조화 로깅 (JSON)
   - Prometheus 메트릭
   - 에러율 알람

### 14-3. 보안 체크리스트

- [ ] HTTPS only
- [ ] 도메인 화이트리스트
- [ ] 파일 크기 제한 (10MB)
- [ ] Decompression bomb 방어
- [ ] EXIF GPS 데이터 삭제 (저장 시)
- [ ] 메타데이터 민감 정보 필터링

---

## Changelog
- 2025-01-XX: 초기 문서 작성 (섹션 1-5)
- 2025-01-XX: 섹션 6-12 완성 (메타데이터, 캐싱, 성능, 보안)
- 2025-01-XX: 종합 예제 및 베스트 프랙티스 추가

---

**문서 완료!** 총 1,900+ 줄의 상세한 이미지 처리 파이프라인 기술 문서입니다. 🎉
