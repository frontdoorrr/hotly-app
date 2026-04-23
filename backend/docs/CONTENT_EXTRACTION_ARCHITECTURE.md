# 콘텐츠 추출 아키텍처

## 📋 현재 상태 (Phase 1 - Mock Data)

### 구현 완료
- ✅ Mock 데이터 기반 콘텐츠 추출
- ✅ 멀티모달 AI 분석 (Gemini 2.0 Flash)
- ✅ 이미지 처리 파이프라인 (ImageProcessor)
- ✅ 텍스트 처리 (TextProcessor)
- ✅ 통합 오케스트레이터 (MultimodalOrchestrator)

### Mock 데이터 시나리오 (URL 해시 기반)

ContentExtractor는 현재 5가지 현실적인 한국어 시나리오를 제공합니다:

1. **성수동 카페**: 북유럽 감성, 브런치, 루프탑
2. **강남 고깃집**: 숙성 한우, 기념일 맛집
3. **홍대 디저트 카페**: 티라미수, 인테리어
4. **이태원 이탈리안**: 파스타, 와인
5. **여의도 오피스 카페**: 직장인 핫플, 브런치

URL의 MD5 해시를 사용하여 시나리오를 선택하므로, 같은 URL은 항상 같은 결과를 반환합니다.

---

## 🚀 향후 계획 (별도 프로젝트)

### Option 1: YouTube Data API v3 (권장)
```
✅ 공식 API
✅ 무료 (10,000 units/day)
✅ 안정적
❌ YouTube만 지원
```

**구현 예시:**
```python
import googleapiclient.discovery

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
request = youtube.videos().list(part="snippet,statistics", id=video_id)
response = request.execute()
```

### Option 2: OpenGraph 메타태그 파싱
```
✅ 가볍고 빠름
✅ 대부분의 SNS 지원
⚠️  제한적인 정보
❌ 이미지는 썸네일만
```

**구현 예시:**
```python
import httpx
from bs4 import BeautifulSoup

response = await httpx.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
title = soup.find('meta', property='og:title')['content']
description = soup.find('meta', property='og:description')['content']
image = soup.find('meta', property='og:image')['content']
```

### Option 3: 전용 크롤링 마이크로서비스
```
✅ 모든 플랫폼 지원
✅ 상세한 데이터 추출
❌ 불안정 (API 변경)
❌ ToS 위반 가능
❌ 리소스 집약적
```

**권장 아키텍처:**
```
┌─────────────────────────────────────────┐
│ Content Extraction Microservice         │
│ (별도 프로젝트)                          │
├─────────────────────────────────────────┤
│ - Playwright/Selenium                    │
│ - Rate Limiting                          │
│ - Error Retry                            │
│ - Result Caching (24h)                   │
└─────────────────────────────────────────┘
            ↓ REST API
┌─────────────────────────────────────────┐
│ ArchyAI Backend                            │
│ (현재 프로젝트)                          │
├─────────────────────────────────────────┤
│ - HTTP Request로 크롤링 결과 가져오기    │
│ - Multimodal Analysis (Gemini)          │
│ - Place DB 저장                          │
└─────────────────────────────────────────┘
```

---

## 🏗️ 통합 가이드 (미래)

### 1단계: ContentExtractor 수정

```python
class ContentExtractor:
    async def extract_content(self, url: str) -> ExtractedContent:
        platform = self._detect_platform(url)

        # Try external crawling service
        try:
            if platform == PlatformType.YOUTUBE:
                return await self._extract_youtube_official(url)
            else:
                return await self._extract_from_crawling_service(url)
        except Exception:
            # Fallback to OpenGraph
            return await self._extract_opengraph(url)

    async def _extract_youtube_official(self, url: str):
        """YouTube Data API v3 사용"""
        video_id = self._extract_video_id(url)
        # ... API 호출

    async def _extract_from_crawling_service(self, url: str):
        """외부 크롤링 서비스 호출"""
        response = await httpx.post(
            "https://crawler-service.internal/extract",
            json={"url": url},
            timeout=30
        )
        # ... 결과 파싱

    async def _extract_opengraph(self, url: str):
        """OpenGraph 메타태그 파싱 (Fallback)"""
        # ... httpx + BeautifulSoup
```

### 2단계: 환경 변수 설정

```bash
# .env
YOUTUBE_API_KEY=your_youtube_api_key
CRAWLER_SERVICE_URL=https://crawler-service.internal
ENABLE_REAL_CRAWLING=true  # false면 mock 데이터 사용
```

### 3단계: 배포

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - ENABLE_REAL_CRAWLING=true
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}

  # Optional: 별도 크롤링 서비스
  crawler:
    image: your-crawler-service:latest
    deploy:
      replicas: 2  # 부하 분산
```

---

## 📊 현재 vs 미래 비교

| 항목 | 현재 (Phase 1) | 미래 (Phase 2) |
|------|---------------|---------------|
| 콘텐츠 추출 | Mock 데이터 | 실제 API/크롤링 |
| 이미지 | 없음 (텍스트만) | 실제 이미지 다운로드 |
| 응답 시간 | ~2초 | ~5-10초 |
| 정확도 | 제한적 | 높음 |
| 비용 | 무료 | API 할당량 |
| 안정성 | 매우 높음 | 중간 |

---

## 🎯 권장 사항

### 개발 환경
- ✅ **Mock 데이터 사용** (현재 상태 유지)
- Gemini API 할당량 절약
- 빠른 개발 및 테스트

### 프로덕션 환경
- ✅ **YouTube**: Official API 사용
- ⚠️ **Instagram**: OpenGraph 또는 별도 서비스
- ⚠️ **Naver Blog**: OpenGraph 또는 별도 서비스

### 스케일링 전략
1. Phase 1: Mock 데이터로 MVP 출시
2. Phase 2: YouTube API 통합
3. Phase 3: OpenGraph 파서 추가
4. Phase 4: 전용 크롤링 서비스 (필요시)

---

## 📚 참고 문서

- [YouTube Data API v3](https://developers.google.com/youtube/v3/docs)
- [OpenGraph Protocol](https://ogp.me/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Multimodal Implementation](./MULTIMODAL_IMPLEMENTATION.md)
