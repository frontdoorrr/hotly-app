# PRD: 소셜 미디어 콘텐츠 종합 분석 시스템

**버전**: 2.0
**작성일**: 2025-01-06
**상태**: 승인됨 (Approved)
**담당**: link-analyzer 마이크로서비스

---

## 📋 Executive Summary

멀티 플랫폼 소셜 미디어 콘텐츠(Instagram, TikTok, YouTube, YouTube Shorts)를 종합적으로 분석하여 hotly-app의 핵심 데이터를 제공하는 시스템. 영상, 사진, 텍스트를 구분하여 분석하고, 음식점/카페, 여행지, 제품 리뷰, 건강 정보 등 다양한 콘텐츠를 자동으로 분류하고 핵심 정보를 추출한다.

### 목표
- **멀티 플랫폼 지원**: Instagram, TikTok, YouTube, YouTube Shorts
- **영상/사진/텍스트 구분 분석**: 플랫폼별 특성에 맞는 처리 파이프라인
- **Gemini 비디오 분석**: YouTube는 URL 직접 전달, 기타는 다운로드 후 분석
- AI 기반 자동 카테고리 분류 및 정보 추출
- **프로토타입 중심**: 기능 검증 우선, 단순한 동기 처리
- 비용 효율적인 MVP 구현 (월 ~$10)

### 범위
- **Phase 1 (3주)**: 프로토타입 구현 - 동기 처리, 기능 검증
- **Phase 2 (향후)**: 비동기 처리 추가, 확장성 개선
- **Phase 3 (향후)**: 프로덕션 준비, 월 10,000개 이상 대응

---

## 🎯 사용자 요구사항

### 분석 범위
1. **음식점/카페 정보**
   - 메뉴, 가격대, 특징
   - 분위기, 주차, 편의시설
   - 영업시간, 위치

2. **여행지/관광지 정보**
   - 위치, 입장료, 운영시간
   - 주요 볼거리, 추천 활동
   - 계절별 특징

3. **제품 리뷰**
   - 제품 정보, 가격
   - 장단점, 사용 후기
   - 구매처 정보

4. **건강 정보**
   - 운동, 식단, 웰니스
   - 전문가 조언, 팁

5. **생활 지식**
   - 생활 팁, 노하우
   - DIY, 인테리어 등

### 분석 우선순위
- **최우선**: 모든 비디오의 음성 전사 + 프레임 OCR
- **중요**: 이미지 내 텍스트 추출 (메뉴판, 간판 등)
- **필수**: AI 기반 자동 카테고리 분류

---

## 🏗️ 시스템 아키텍처

### 전체 흐름
```
[사용자 요청: 소셜 미디어 URL]
    ↓
[link-analyzer API Gateway]
    ↓
[플랫폼 감지 & 라우팅]
    ├─ YouTube/Shorts → [YouTube 파이프라인]
    ├─ Instagram → [Instagram 파이프라인]
    └─ TikTok → [TikTok 파이프라인]
    ↓
[플랫폼별 메타데이터 추출]
    ├─ [YouTube] → YouTube Data API v3
    │   - 제목, 설명, 태그
    │   - 채널 정보
    │   - 공개 URL (비디오)
    │
    ├─ [Instagram] → yt-dlp + 메타데이터 파싱
    │   - 캡션, 해시태그
    │   - 위치 정보 (선택적)
    │   - 이미지/비디오 다운로드
    │
    └─ [TikTok] → yt-dlp + 메타데이터 파싱
        - 설명, 해시태그
        - 음악 정보
        - 비디오 다운로드
    ↓
[콘텐츠 타입별 분석 라우팅]
    ├─ [비디오] → Gemini Video Analysis
    │   ├─ YouTube: URL 직접 전달 (다운로드 불필요)
    │   ├─ Instagram/TikTok: File API 업로드
    │   └─ Gemini 통합 분석
    │       - 비디오 프레임 분석 (1fps)
    │       - 음성 전사
    │       - 프레임 내 텍스트 추출 (OCR)
    │
    ├─ [이미지] → OCR Pipeline
    │   - Gemini Vision API로 통합 분석
    │   - 이미지 내 텍스트, 객체, 장면 인식
    │
    └─ [텍스트] → 항상 추출
        - 제목/캡션
        - 해시태그
        - 설명
    ↓
[통합 데이터 구조화]
    {
        "platform": "youtube|instagram|tiktok",
        "content_type": "video|image|carousel",
        "text_data": {
            "title": "제목",
            "caption": "설명/캡션",
            "hashtags": ["태그1", "태그2"],
            "extracted_text": ["OCR 텍스트"]
        },
        "video_analysis": {
            "transcript": "음성 전사",
            "visual_elements": ["장면 설명"]
        },
        "metadata": {...}
    }
    ↓
[AI 분석 (Google Gemini)]
    ├─ 카테고리 분류
    │   - 주 카테고리: 음식점/카페/여행지/제품/건강/생활
    │   - 서브 카테고리: 한식/양식/카페/호텔 등
    │
    ├─ 핵심 정보 추출
    │   - 장소명, 위치, 연락처
    │   - 메뉴/제품, 가격대
    │   - 영업시간, 편의시설
    │   - 주요 특징
    │
    ├─ 감성 분석
    │   - 긍정/부정/중립 평가
    │   - 추천 여부
    │
    └─ 요약 생성
        - 2-3문장 핵심 요약
        - 주요 키워드 추출
    ↓
[PostgreSQL 저장]
    ↓
[응답 반환]
```

### 플랫폼별 처리 전략

| 플랫폼 | 메타데이터 추출 | 비디오 처리 | 비용 효율성 |
|--------|----------------|-------------|------------|
| **YouTube** | YouTube Data API v3 | Gemini URL 직접 (무료*) | ⭐⭐⭐ 최고 |
| **YouTube Shorts** | YouTube Data API v3 | Gemini URL 직접 (무료*) | ⭐⭐⭐ 최고 |
| **Instagram** | yt-dlp | 다운로드 → File API | ⭐⭐ 보통 |
| **TikTok** | yt-dlp | 다운로드 → File API | ⭐⭐ 보통 |

*YouTube는 일일 8시간 제한

---

## 🛠️ 기술 스택

### 외부 서비스
| 서비스 | 용도 | 비용 (월 1,000개 기준) | 선택 이유 |
|--------|-----|---------------------|----------|
| **YouTube Data API v3** | YouTube 메타데이터 추출 | $0 (무료 쿼터) | 공식 API, 안정적 |
| **Google Gemini 2.5** | 비디오/이미지 통합 분석 | 기존 API 활용 | 비디오 URL 직접 지원, OCR+음성 전사 통합 |
| **yt-dlp** | Instagram/TikTok 다운로드 | 무료 (오픈소스) | 범용 다운로더, 활발한 개발 |

### 오픈소스 라이브러리
```python
# 플랫폼별 데이터 추출
yt-dlp==2024.1.1              # Instagram/TikTok 비디오 다운로드
google-api-python-client==2.110.0  # YouTube Data API v3
requests==2.31.0              # HTTP 요청
httpx==0.26.0                 # 비동기 HTTP

# AI/ML (통합)
google-genai==0.3.0           # Gemini 2.5 API (비디오/이미지/텍스트 통합)

# 유틸리티
pydantic==2.5.3               # 데이터 검증
python-dotenv==1.0.0          # 환경 변수
```

### 주요 변경 사항
- **Deepgram 제거**: Gemini가 비디오 음성 전사 내장 지원
- **Tesseract/Google Vision 제거**: Gemini가 OCR 내장 지원
- **FFmpeg/OpenCV 제거**: Gemini가 프레임 추출/분석 자동 처리
- **Apify 제거**: yt-dlp로 Instagram/TikTok 직접 처리

### 인프라
- **백엔드**: FastAPI (link-analyzer 서비스)
- **데이터베이스**: PostgreSQL (기존)
- **처리 방식**: 동기 처리 (async/await)
- **컨테이너**: Docker Compose

---

## 📦 구현 단계별 계획

### Phase 1: 기반 인프라 (3-4일)

#### 1.1 프로젝트 구조
```
link-analyzer/
├── app/
│   ├── services/
│   │   ├── platform/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # 기본 플랫폼 인터페이스
│   │   │   ├── youtube.py           # YouTube 메타데이터 추출
│   │   │   ├── instagram.py         # Instagram yt-dlp 추출
│   │   │   └── tiktok.py            # TikTok yt-dlp 추출
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_video.py      # Gemini 비디오 분석
│   │   │   ├── gemini_image.py      # Gemini 이미지 분석
│   │   │   └── content_classifier.py # AI 분류/분석
│   │   └── link_analyzer_service.py # 통합 분석 서비스
│   ├── api/v1/endpoints/
│   │   └── analyze.py               # 통합 분석 엔드포인트
│   ├── schemas/
│   │   └── analysis.py              # Pydantic 스키마
│   └── models/
│       └── analysis.py              # DB 모델
└── tests/
    ├── unit/
    │   ├── test_platform_extractors.py
    │   └── test_gemini_analysis.py
    └── integration/
        └── test_analysis_pipeline.py
```

#### 1.2 환경 변수 설정
```bash
# .env 추가 항목
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_data_api_key

# 작업 설정
MAX_VIDEO_DURATION=600  # 10분 (YouTube Shorts 최대)
MAX_VIDEO_SIZE_MB=100
REQUEST_TIMEOUT=120  # API 요청 타임아웃 (초)
YOUTUBE_DAILY_QUOTA_LIMIT=8  # 시간 (Gemini 무료 제한)
```

#### 1.3 Docker Compose 업데이트
```yaml
# docker-compose.yml - 추가 설정 불필요
# 기존 link-analyzer, postgres 서비스만 사용
```

---

### Phase 2: 플랫폼별 메타데이터 추출 (3-4일)

#### 2.1 기본 플랫폼 인터페이스

**파일**: `app/services/platform/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class Platform(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"

class ContentType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"

class PlatformExtractor(ABC):
    """플랫폼별 메타데이터 추출 기본 인터페이스"""

    @abstractmethod
    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        플랫폼별 메타데이터 추출

        Returns:
            {
                'platform': Platform,
                'content_type': ContentType,
                'url': str,
                'title': str,
                'description': str,
                'hashtags': List[str],
                'media_urls': Optional[List[str]],  # 다운로드가 필요한 경우
                'metadata': Dict[str, Any]  # 플랫폼별 추가 정보
            }
        """
        pass

    @staticmethod
    def detect_platform(url: str) -> Optional[Platform]:
        """URL에서 플랫폼 자동 감지"""
        if "youtube.com" in url or "youtu.be" in url:
            return Platform.YOUTUBE
        elif "instagram.com" in url:
            return Platform.INSTAGRAM
        elif "tiktok.com" in url:
            return Platform.TIKTOK
        return None
```

#### 2.2 YouTube 추출기

**파일**: `app/services/platform/youtube.py`

```python
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeExtractor(PlatformExtractor):
    """YouTube Data API v3 기반 메타데이터 추출"""

    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        YouTube 비디오 메타데이터 추출

        Returns:
            {
                'platform': 'youtube',
                'content_type': 'video',
                'video_id': str,
                'title': str,
                'description': str,
                'tags': List[str],
                'channel_title': str,
                'published_at': datetime,
                'duration': str,
                'view_count': int,
                'media_urls': None  # YouTube는 다운로드 불필요
            }
        """
        video_id = self._extract_video_id(url)
        response = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()

        return self._parse_response(response)

    def _extract_video_id(self, url: str) -> str:
        """YouTube URL에서 비디오 ID 추출"""
        # youtube.com/watch?v=VIDEO_ID
        # youtu.be/VIDEO_ID
        pass

    @staticmethod
    def is_shorts(url: str) -> bool:
        """YouTube Shorts 여부 판단"""
        return "/shorts/" in url
```

#### 2.3 Instagram/TikTok 추출기

**파일**: `app/services/platform/instagram.py` & `tiktok.py`

```python
import yt_dlp

class InstagramExtractor(PlatformExtractor):
    """yt-dlp 기반 Instagram 메타데이터 추출 및 다운로드"""

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Instagram 게시글 메타데이터 추출 및 미디어 다운로드

        Returns:
            {
                'platform': 'instagram',
                'content_type': 'video|image|carousel',
                'caption': str,
                'hashtags': List[str],
                'location': Optional[str],
                'media_urls': List[str],  # 다운로드된 파일 경로
                'timestamp': datetime
            }
        """
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp/%(id)s.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return self._parse_info(info)

    def _parse_info(self, info: Dict) -> Dict[str, Any]:
        """yt-dlp 결과 파싱"""
        pass

class TikTokExtractor(PlatformExtractor):
    """yt-dlp 기반 TikTok 메타데이터 추출 및 다운로드"""
    # Instagram과 유사한 구조
    pass
```

---

### Phase 3: Gemini 통합 분석 파이프라인 (3-4일)

#### 3.1 Gemini 비디오 분석

**파일**: `app/services/analysis/gemini_video.py`

```python
from google import genai
from google.genai import types

class GeminiVideoAnalyzer:
    """Gemini 2.5 기반 비디오 통합 분석"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def analyze_video_url(self, url: str, prompt: str) -> Dict[str, Any]:
        """
        YouTube URL 직접 분석 (다운로드 불필요)

        Args:
            url: YouTube 공개 URL
            prompt: 분석 프롬프트

        Returns:
            {
                'transcript': str,  # 음성 전사
                'extracted_text': List[str],  # 프레임 내 텍스트
                'visual_elements': List[str],  # 장면 설명
                'analysis': Dict  # AI 분석 결과
            }
        """
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_uri(
                    file_uri=url,
                    mime_type="video/mp4"
                ),
                types.Part.from_text(prompt)
            ]
        )
        return self._parse_response(response)

    async def analyze_video_file(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """
        로컬 비디오 파일 분석 (Instagram/TikTok)

        Args:
            file_path: 다운로드된 비디오 파일 경로
            prompt: 분석 프롬프트
        """
        # File API로 업로드 후 분석
        with open(file_path, 'rb') as f:
            video_bytes = f.read()

        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part(
                    inline_data=types.Blob(
                        data=video_bytes,
                        mime_type='video/mp4'
                    )
                ),
                types.Part(text=prompt)
            ]
        )
        return self._parse_response(response)

#### 3.2 Gemini 이미지 분석

**파일**: `app/services/analysis/gemini_image.py`

```python
class GeminiImageAnalyzer:
    """Gemini Vision API 기반 이미지 분석"""

    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        이미지 통합 분석 (OCR + 객체 인식 + 장면 이해)

        Returns:
            {
                'extracted_text': str,  # OCR 텍스트
                'objects': List[str],  # 감지된 객체
                'scene_description': str,  # 장면 설명
                'analysis': Dict  # AI 분석 결과
            }
        """
        pass
```

---

### Phase 4: AI 분석 파이프라인 (3-4일)

#### 4.1 콘텐츠 분류기

**파일**: `app/services/instagram/content_classifier.py`

```python
import google.generativeai as genai

class ContentClassifier:
    """Google Gemini 기반 콘텐츠 분석"""

    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def classify(self, content: ContentData) -> Classification:
        """
        콘텐츠 카테고리 분류

        Args:
            content: {
                'caption': str,
                'ocr_texts': List[str],
                'transcript': Optional[str],
                'hashtags': List[str],
                'location': Optional[Dict]
            }

        Returns:
            {
                'primary_category': str,  # 음식점/카페/여행지/제품/건강/생활
                'sub_categories': List[str],  # 한식/양식/디저트 등
                'tags': List[str],  # #분위기좋은 #데이트코스
                'confidence': float
            }
        """

        prompt = self._build_classification_prompt(content)
        response = await self.model.generate_content_async(prompt)
        return self._parse_classification(response.text)
```

#### 4.2 정보 추출기

```python
class InformationExtractor:
    """핵심 정보 추출"""

    async def extract(self, content: ContentData) -> ExtractedInfo:
        """
        Returns:
            {
                'place_info': {
                    'name': str,
                    'location': str,
                    'phone': Optional[str],
                    'hours': Optional[str],
                    'address': Optional[str]
                },
                'menu_items': List[{
                    'name': str,
                    'price': Optional[str],
                    'description': Optional[str]
                }],
                'features': List[str],  # 주차가능/반려동물동반/키즈존
                'price_range': Optional[str],  # ₩₩ / ₩₩₩
                'recommended_for': List[str]  # 데이트/가족모임/혼밥
            }
        """
```

#### 4.3 감성 분석 & 요약

```python
class ContentAnalyzer:
    """감성 분석 및 요약"""

    async def analyze_sentiment(self, text: str) -> Sentiment:
        """
        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'score': float,  # -1.0 ~ 1.0
                'aspects': {  # 측면별 감성
                    'food_quality': float,
                    'service': float,
                    'atmosphere': float,
                    'value': float
                }
            }
        """

    async def generate_summary(self, content: ContentData) -> str:
        """2-3문장 핵심 요약"""

    async def extract_keywords(self, content: ContentData) -> List[str]:
        """주요 키워드 추출"""
```

---

### Phase 5: 통합 분석 서비스 (1-2일)

#### 5.1 통합 분석 파이프라인

**파일**: `app/services/instagram/analysis_service.py`

```python
from app.services.instagram import (
    ApifyInstagramClient,
    MediaDownloader,
    VideoFrameExtractor,
    AudioTranscriber,
    OCRService,
    ContentClassifier,
    InformationExtractor,
    ContentAnalyzer
)

class InstagramAnalysisService:
    """Instagram 게시글 통합 분석 서비스"""

    def __init__(self):
        self.apify_client = ApifyInstagramClient(settings.APIFY_API_KEY)
        self.downloader = MediaDownloader()
        self.video_analyzer = VideoFrameExtractor()
        self.transcriber = AudioTranscriber(settings.DEEPGRAM_API_KEY)
        self.ocr_service = OCRService(settings.GOOGLE_APPLICATION_CREDENTIALS)
        self.classifier = ContentClassifier(settings.GEMINI_API_KEY)
        self.extractor = InformationExtractor(settings.GEMINI_API_KEY)
        self.analyzer = ContentAnalyzer(settings.GEMINI_API_KEY)

    async def analyze_post(self, url: str) -> AnalysisResult:
        """
        Instagram 게시글 종합 분석 (동기)

        Returns:
            AnalysisResult: 완성된 분석 결과
        """
        try:
            # 1. Apify로 메타데이터 추출
            post_data = await self.apify_client.extract_post(url)

            # 2. 미디어 다운로드
            media_files = await self.downloader.download_multiple(post_data['media_urls'])

            # 3. 미디어 타입별 처리
            texts = []
            transcript = None

            for media_file in media_files:
                if post_data['is_video']:
                    # 비디오 분석
                    frames = self.video_analyzer.extract_keyframes(media_file)

                    # 음성 전사
                    transcript = await self.transcriber.transcribe(media_file)
                    texts.append(transcript['text'])

                    # 프레임 OCR
                    for frame in frames:
                        ocr_result = await self.ocr_service.extract_text(frame)
                        if ocr_result['text']:
                            texts.append(ocr_result['text'])
                else:
                    # 이미지 OCR
                    image = cv2.imread(str(media_file))
                    ocr_result = await self.ocr_service.extract_text(image)
                    if ocr_result['text']:
                        texts.append(ocr_result['text'])

            # 4. AI 분석
            content_data = {
                'caption': post_data['caption'],
                'ocr_texts': texts,
                'transcript': transcript['text'] if transcript else None,
                'hashtags': post_data['hashtags'],
                'location': post_data.get('location')
            }

            classification = await self.classifier.classify(content_data)
            extracted_info = await self.extractor.extract(content_data)
            sentiment = await self.analyzer.analyze_sentiment(post_data['caption'])
            summary = await self.analyzer.generate_summary(content_data)

            # 5. 결과 통합
            analysis_result = {
                'url': url,
                'post_data': post_data,
                'classification': classification,
                'extracted_info': extracted_info,
                'sentiment': sentiment,
                'summary': summary,
                'analyzed_at': datetime.utcnow()
            }

            # 6. DB 저장
            await db.save_analysis(analysis_result)

            # 7. 임시 파일 정리
            self.downloader.cleanup_temp_files(media_files)

            return analysis_result

        except Exception as exc:
            # 에러 로깅 및 재발생
            logger.error(f"Analysis failed for {url}: {str(exc)}")
            raise
```

---

### Phase 6: API 엔드포인트 (2일)

#### 6.1 Pydantic 스키마

**파일**: `app/schemas/instagram.py`

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InstagramAnalysisRequest(BaseModel):
    """분석 요청"""
    url: HttpUrl = Field(..., description="Instagram 게시글 URL")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            'include_video_transcription': True,
            'include_ocr': True
        }
    )

class Classification(BaseModel):
    """카테고리 분류 결과"""
    primary_category: str
    sub_categories: List[str]
    tags: List[str]
    confidence: float

class PlaceInfo(BaseModel):
    """장소 정보"""
    name: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    hours: Optional[str]
    address: Optional[str]

class MenuItem(BaseModel):
    """메뉴 항목"""
    name: str
    price: Optional[str]
    description: Optional[str]

class ExtractedInfo(BaseModel):
    """추출된 정보"""
    place_info: Optional[PlaceInfo]
    menu_items: List[MenuItem]
    features: List[str]
    price_range: Optional[str]
    recommended_for: List[str]

class Sentiment(BaseModel):
    """감성 분석 결과"""
    sentiment: str  # positive/negative/neutral
    score: float
    aspects: Dict[str, float]

class InstagramAnalysisResponse(BaseModel):
    """분석 응답"""
    url: str
    post_data: Dict[str, Any]
    classification: Classification
    extracted_info: ExtractedInfo
    sentiment: Sentiment
    summary: str
    analyzed_at: datetime
```

#### 6.2 API 엔드포인트

**파일**: `app/api/v1/endpoints/instagram.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.instagram import (
    InstagramAnalysisRequest,
    InstagramAnalysisResponse
)
from app.services.instagram.analysis_service import InstagramAnalysisService

router = APIRouter()
analysis_service = InstagramAnalysisService()

@router.post("/analyze", response_model=InstagramAnalysisResponse)
async def analyze_instagram_post(
    request: InstagramAnalysisRequest
):
    """
    Instagram 게시글 분석 (동기 처리)

    - 이미지/비디오 다운로드
    - 음성 전사 및 OCR
    - AI 기반 분류 및 정보 추출

    처리 시간: 평균 30-60초
    """
    try:
        result = await analysis_service.analyze_post(str(request.url))
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{url:path}")
async def get_cached_analysis(url: str):
    """
    기존 분석 결과 조회

    이미 분석된 게시글의 결과를 DB에서 조회
    """
    try:
        result = await db.get_analysis_by_url(url)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Phase 7: 테스트 & 최적화 (2-3일)

#### 7.1 단위 테스트

**파일**: `tests/unit/test_instagram_services.py`

```python
import pytest
from app.services.instagram import (
    ApifyInstagramClient,
    VideoFrameExtractor,
    AudioTranscriber,
    OCRService,
    ContentClassifier
)

class TestApifyClient:
    """Apify 클라이언트 테스트"""

    @pytest.mark.asyncio
    async def test_extract_post_success(self):
        """정상 게시글 콘텐츠 추출"""

    @pytest.mark.asyncio
    async def test_extract_post_deleted(self):
        """삭제된 게시글 처리"""

    @pytest.mark.asyncio
    async def test_extract_post_inaccessible(self):
        """접근 불가 게시글 처리"""

class TestVideoAnalysis:
    """비디오 분석 테스트"""

    def test_extract_frames(self):
        """프레임 추출 정확도"""

    @pytest.mark.asyncio
    async def test_transcribe_audio(self):
        """음성 전사 정확도"""

class TestOCR:
    """OCR 테스트"""

    @pytest.mark.asyncio
    async def test_ocr_menu(self):
        """메뉴판 OCR 정확도"""

    @pytest.mark.asyncio
    async def test_ocr_fallback(self):
        """Google Vision 폴백"""

class TestAIClassification:
    """AI 분류 테스트"""

    @pytest.mark.asyncio
    async def test_classify_restaurant(self):
        """음식점 분류 정확도"""

    @pytest.mark.asyncio
    async def test_extract_menu_items(self):
        """메뉴 추출 정확도"""
```

#### 7.2 통합 테스트

**파일**: `tests/integration/test_instagram_pipeline.py`

```python
class TestInstagramPipeline:
    """전체 파이프라인 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_pipeline_image_post(self):
        """이미지 게시글 전체 파이프라인"""

    @pytest.mark.asyncio
    async def test_full_pipeline_video_post(self):
        """비디오 게시글 전체 파이프라인"""

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """배치 처리 성능 테스트"""

    @pytest.mark.asyncio
    async def test_duplicate_prevention(self):
        """중복 분석 방지 테스트"""
```

#### 7.3 성능 벤치마크

```python
# 샘플 10개 게시글로 측정
# - 평균 처리 시간
# - API 호출 비용
# - 중복 분석 방지율
# - 에러율
```

---

## 💰 비용 분석

### MVP 비용 (월 1,000개 게시물)

**가정**: YouTube 40%, Instagram 40%, TikTok 20%

| 항목 | 수량/사용량 | 단가 | 월 비용 |
|-----|-----------|------|---------|
| **YouTube Data API v3** | 1,000 requests | 무료 (10,000 쿼터/일) | $0 |
| **yt-dlp (Instagram/TikTok)** | 600 downloads | 무료 (오픈소스) | $0 |
| **Gemini 2.5 비디오 분석** | | | |
| - YouTube (URL 직접) | 400 videos × 1분 | 무료 (일일 8시간) | $0 |
| - Instagram/TikTok | 600 videos × 1분 × 300 tokens/sec | $0.075/1M tokens | ~$2.70 |
| **Gemini 이미지 분석** | 200 images | $0.00025/image | $0.05 |
| **Gemini 텍스트 분석** | 1,000 requests × 2K tokens | $0.075/1M tokens | $0.15 |
| **FastAPI 서버** | 기존 인프라 | | $0 |
| **스토리지** | ~5GB (임시) | S3 $0.023/GB | $0.12 |
| **네트워크** | ~50GB | 무료 티어 | $0 |
| **총계** | | | **~$3.02/월** |

### 비용 절감 핵심
- ✅ **Deepgram 제거** ($4.80 → $0): Gemini 내장 음성 전사
- ✅ **Google Vision 제거** ($0.38 → $0): Gemini 내장 OCR
- ✅ **Apify 제거** ($0 → $0): yt-dlp로 대체
- ✅ **YouTube 최적화**: URL 직접 전달로 다운로드 비용 제거

### 확장 비용 (월 10,000개 게시물)

**가정**: YouTube 40%, Instagram 40%, TikTok 20%

| 항목 | 수량/사용량 | 단가 | 월 비용 |
|-----|-----------|------|---------|
| **YouTube Data API v3** | 10,000 requests | 무료 (쿼터 내) | $0 |
| **yt-dlp** | 6,000 downloads | 무료 | $0 |
| **Gemini 비디오 분석** | | | |
| - YouTube | 4,000 videos × 1분 | 무료 (제한 초과 시 유료) | ~$36* |
| - Instagram/TikTok | 6,000 videos × 1분 | $0.075/1M tokens | ~$27 |
| **Gemini 이미지 분석** | 2,000 images | $0.00025/image | $0.50 |
| **Gemini 텍스트 분석** | 10,000 requests | $0.075/1M tokens | $1.50 |
| **인프라 확장** | Autoscaling | | $30 |
| **스토리지** | ~50GB | S3 | $1.15 |
| **CDN** | ~500GB | CloudFront | $10 |
| **총계** | | | **~$106/월** |

*YouTube 일일 8시간 제한 초과 시 유료 전환 가정

---

## 📅 구현 일정

### Week 1: 기반 인프라 & Instagram 추출

**Day 1-2**: 프로젝트 구조 및 환경 설정
- [ ] 디렉토리 구조 생성
- [ ] Dependencies 설치
- [ ] Docker Compose 업데이트
- [ ] 환경 변수 설정
- [ ] Apify 계정 생성 및 API 키 획득

**Day 3-4**: Apify 클라이언트 구현
- [ ] ApifyInstagramClient 구현
- [ ] 에러 처리 및 재시도 로직
- [ ] MediaDownloader 구현
- [ ] 단위 테스트 작성
- [ ] 10개 샘플로 테스트

**산출물**:
- ✅ Apify API 통합 완료
- ✅ 기본 데이터 추출 가능
- ✅ 이미지/비디오 다운로드 기능

---

### Week 2: 비디오 분석 파이프라인

**Day 5-6**: 프레임 추출 & 음성 전사
- [ ] FFmpeg 기반 프레임 추출 구현
- [ ] Deepgram 계정 생성 및 API 통합
- [ ] AudioTranscriber 구현
- [ ] 비디오 분석 단위 테스트
- [ ] 5개 샘플 비디오로 정확도 검증

**Day 7-8**: OCR 파이프라인
- [ ] Tesseract OCR 구현
- [ ] Google Cloud Vision 계정 설정
- [ ] OCRService 하이브리드 구현
- [ ] 이미지 전처리 최적화
- [ ] OCR 정확도 테스트

**산출물**:
- ✅ 비디오 음성 전사 기능
- ✅ 프레임 OCR 기능
- ✅ 이미지 OCR 기능

---

### Week 3: AI 분석 & 통합 서비스

**Day 9-10**: AI 분류 및 정보 추출
- [ ] ContentClassifier 구현
- [ ] InformationExtractor 구현
- [ ] ContentAnalyzer 구현
- [ ] Gemini 프롬프트 최적화
- [ ] 분류 정확도 테스트

**Day 11-12**: 통합 분석 서비스
- [ ] InstagramAnalysisService 구현
- [ ] 전체 파이프라인 통합
- [ ] 에러 처리 및 재시도 로직
- [ ] 타임아웃 관리
- [ ] 통합 테스트

**산출물**:
- ✅ AI 기반 자동 분류
- ✅ 핵심 정보 추출
- ✅ 통합 분석 파이프라인

---

### Week 4: API & 테스트 & 배포

**Day 13-14**: API 엔드포인트
- [ ] Pydantic 스키마 정의
- [ ] API 엔드포인트 구현 (동기 처리)
- [ ] API 문서화 (Swagger)
- [ ] API 통합 테스트

**Day 15-16**: 테스트 & 최적화
- [ ] 전체 파이프라인 테스트 (30개 샘플)
- [ ] 비용 측정 및 최적화
- [ ] 성능 벤치마크
- [ ] 에러 핸들링 강화
- [ ] 로깅 설정

**Day 17**: 배포 & 문서화
- [ ] Docker 환경 배포
- [ ] API 사용 가이드 작성
- [ ] README 업데이트
- [ ] 최종 검증

**산출물**:
- ✅ 단순한 Instagram 분석 API (프로토타입)
- ✅ 기본 테스트 커버리지
- ✅ Docker 배포 완료

---

## ⚠️ 주요 고려사항

### 법적 준수

#### 1. 플랫폼별 ToS 준수

**YouTube**
- ✅ **공식 API 사용**: YouTube Data API v3로 ToS 준수
- ✅ **공개 영상만**: 비공개/제한된 콘텐츠 접근 금지
- ✅ **API 쿼터 준수**: 일일 쿼터 제한 준수
- ✅ **비디오 다운로드 금지**: Gemini URL 직접 전달로 다운로드 회피

**Instagram/TikTok**
- ⚠️ **yt-dlp 사용**: 공개 게시물만, 법적 리스크 인지
- ✅ **Rate limiting**: 합리적인 요청 빈도 유지
- ❌ **인증 우회 금지**: 로그인 없이 공개 데이터만
- ⚠️ **플랫폼 정책 변경 모니터링**: yt-dlp 차단 가능성

#### 2. 개인정보 보호
- ✅ **GDPR/CCPA 준수**: 사용자 데이터 최소 수집
- ✅ **익명화**: 개인 식별 정보 제거
- ✅ **데이터 보유 기간**: 24시간 캐시, 분석 결과만 장기 보관
- ✅ **삭제 요청 처리**: 사용자 요청 시 데이터 삭제

#### 3. 저작권
- ✅ **페어 유즈**: 분석 목적의 제한적 사용
- ✅ **출처 표시**: Instagram 원본 링크 유지
- ❌ **재배포 금지**: 원본 이미지/비디오 재배포 금지
- ✅ **요약/분석 결과만 제공**: 원본 콘텐츠 저장 최소화

### 기술적 리스크

#### 1. 플랫폼 구조 변경
- **위험도**: 중간 (Instagram/TikTok), 낮음 (YouTube)
- **완화책**:
  - YouTube: 공식 API 사용으로 안정적
  - Instagram/TikTok: yt-dlp 자동 업데이트 모니터링
- **백업책**: 플랫폼별 대체 추출 방법 준비

#### 2. Gemini 비용 관리
- **위험도**: 낮음
- **완화책**:
  - YouTube URL 직접 사용으로 비용 최소화
  - Instagram/TikTok만 다운로드하여 비용 제한
  - DB 기반 중복 분석 방지
  - 일일 YouTube 8시간 제한 모니터링
- **모니터링**: 일일 토큰 사용량 추적, 예산 알림

#### 3. 비디오 처리 시간
- **위험도**: 낮음
- **완화책**:
  - Gemini가 자동으로 최적화된 처리
  - YouTube는 다운로드 불필요로 시간 단축
  - 최대 10분 비디오 제한 (YouTube Shorts 대응)
- **목표**: YouTube 평균 20초, Instagram/TikTok 평균 40초

#### 4. yt-dlp 안정성
- **위험도**: 중간
- **완화책**:
  - yt-dlp 버전 고정 및 테스트
  - 플랫폼 차단 시 우아한 실패 처리
  - 에러율 모니터링 및 알림
- **목표**: 성공률 90%+

### 확장 전략

#### Phase 2 (프로토타입 검증 후 - 향후 3개월)
- [ ] **비동기 처리 추가**: Celery + RabbitMQ/Redis 도입
- [ ] **배치 처리**: 여러 게시글 동시 분석
- [ ] Instaloader 폴백 구현
- [ ] 비디오 장면 분할 및 상세 분석
- [ ] 다국어 지원 강화
- [ ] 사용자 피드백 기반 재학습

#### Phase 3 (프로덕션 준비 - 향후 6개월)
- [ ] 커스텀 스크래퍼 (50K+ posts/month)
- [ ] Self-hosted Whisper (비용 최적화)
- [ ] GraphQL API 제공
- [ ] 웹훅 지원
- [ ] 분석 대시보드
- [ ] 모니터링 및 알림 시스템

---

## 📊 성공 지표 (KPI)

### 기능 지표
- [ ] **처리 성공률**: 95% 이상
- [ ] **평균 처리 시간**: 30초 이내 (비디오 포함)
- [ ] **분류 정확도**: 85% 이상

### 비용 지표
- [ ] **월 운영비**: $15 이내 (1,000 posts)
- [ ] **게시물당 비용**: $0.015 이하
- [ ] **중복 분석 방지율**: 80% 이상

### 품질 지표
- [ ] **OCR 정확도**: 90% 이상
- [ ] **음성 전사 정확도**: 95% 이상
- [ ] **API 가용성**: 99% 이상
- [ ] **에러율**: 5% 이하

---

## 📚 참고 자료

### API 문서
- [Google Gemini 2.5 Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Google Gemini API](https://ai.google.dev/docs)

### 오픈소스
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 범용 비디오 다운로더
- [google-api-python-client](https://github.com/googleapis/google-api-python-client) - YouTube API
- [google-genai](https://github.com/googleapis/python-genai) - Gemini Python SDK

### 법적 참고
- [YouTube Terms of Service](https://www.youtube.com/t/terms)
- [Instagram Terms of Service](https://help.instagram.com/581066165581870)
- [TikTok Terms of Service](https://www.tiktok.com/legal/terms-of-service)
- [GDPR Compliance](https://gdpr.eu/)
- [Fair Use Guidelines](https://www.copyright.gov/fair-use/)

---

## 🔄 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|-----|------|----------|-------|
| 1.0 | 2025-11-04 | 초안 작성 (Instagram 전용) | AI Assistant |
| 2.0 | 2025-01-06 | 멀티 플랫폼 지원으로 확장 (YouTube/Instagram/TikTok) | AI Assistant |

### v2.0 주요 변경사항
- ✅ **멀티 플랫폼 지원**: YouTube, YouTube Shorts, Instagram, TikTok
- ✅ **Gemini 통합**: 비디오 음성 전사 + OCR 통합, 외부 서비스 제거
- ✅ **YouTube 최적화**: URL 직접 전달로 다운로드 불필요
- ✅ **비용 절감**: $5.41 → $3.02 (44% 절감)
- ✅ **기술 스택 간소화**: Deepgram, Tesseract, Google Vision, Apify 제거
- ✅ **영상/사진/텍스트 구분 분석**: 플랫폼별 특성 유지

---

**다음 단계**: Phase 1 구현 시작 (기반 인프라 구축)
**예상 완료일**: 2025-02-03 (4주 후)
**리뷰 필요**: 매주 금요일 진행 상황 점검
