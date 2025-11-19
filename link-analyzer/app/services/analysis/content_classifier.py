"""Content classification and information extraction using Gemini."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from google import genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class ContentClassifier:
    """Gemini-based content classification and structured information extraction."""

    def __init__(self, api_key: str):
        """
        Initialize content classifier.

        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'

        # Rate limiting
        self.last_request_time: datetime | None = None
        self.min_request_interval = settings.GEMINI_MIN_REQUEST_INTERVAL

    async def classify(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify content and extract structured information.

        Args:
            content_data: Dictionary containing:
                - caption: Text caption/description
                - ocr_texts: List of extracted texts from OCR
                - transcript: Optional video transcript
                - hashtags: List of hashtags
                - location: Optional location info

        Returns:
            Dictionary containing:
                - primary_category: Main category (음식점/카페/여행지/제품/건강/생활)
                - sub_categories: List of sub-categories
                - place_info: Extracted place information
                - menu_items: List of menu/product items
                - features: List of features (주차가능/반려동물동반 등)
                - price_range: Price range indicator
                - recommended_for: List of recommendations (데이트/가족모임 등)
                - sentiment: Sentiment analysis
                - summary: 2-3 sentence summary
                - keywords: List of keywords
                - confidence: Confidence score (0-1)

        Raises:
            ValueError: If classification fails
        """
        # Apply rate limiting
        await self._apply_rate_limit()

        prompt = self._build_classification_prompt(content_data)

        try:
            response = await self._call_gemini_with_retry(prompt)
            return self._parse_classification(response.text)

        except Exception as e:
            raise ValueError(f"Failed to classify content: {e}")

    async def _apply_rate_limit(self):
        """Apply rate limiting between API requests."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.info(f"Rate limiting: waiting {wait_time:.2f}s before next request")
                await asyncio.sleep(wait_time)

        self.last_request_time = datetime.now()

    @retry(
        stop=stop_after_attempt(settings.GEMINI_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=settings.GEMINI_RETRY_MIN_WAIT,
            max=settings.GEMINI_RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_gemini_with_retry(self, prompt: str):
        """
        Call Gemini API with retry logic.

        Args:
            prompt: Classification prompt

        Returns:
            Gemini API response

        Raises:
            Exception: If all retries fail
        """
        try:
            # Note: google-genai SDK doesn't have async support yet
            # We wrap the sync call to maintain async interface
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=prompt
            )
            return response

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    def _build_classification_prompt(self, content_data: Dict[str, Any]) -> str:
        """
        Build classification prompt from content data.

        Args:
            content_data: Content information

        Returns:
            Structured prompt for Gemini
        """
        prompt_parts = [
            "다음 소셜 미디어 콘텐츠를 분석하여 JSON 형식으로 정보를 추출해주세요.\n",
            "\n=== 콘텐츠 정보 ===\n"
        ]

        if content_data.get('caption'):
            prompt_parts.append(f"캡션: {content_data['caption']}\n")

        if content_data.get('ocr_texts'):
            prompt_parts.append(f"추출된 텍스트: {', '.join(content_data['ocr_texts'])}\n")

        if content_data.get('transcript'):
            prompt_parts.append(f"음성 전사: {content_data['transcript']}\n")

        if content_data.get('hashtags'):
            prompt_parts.append(f"해시태그: {', '.join(content_data['hashtags'])}\n")

        if content_data.get('location'):
            prompt_parts.append(f"위치: {content_data['location']}\n")

        prompt_parts.append("\n=== 요청사항 ===\n")
        prompt_parts.append("""
다음 정보를 JSON 형식으로 추출해주세요:

{
  "primary_category": "음식점|카페|여행지|제품|건강|생활 중 하나",
  "sub_categories": ["한식", "양식", "카페" 등 세부 카테고리 리스트],
  "place_info": {
    "name": "장소명 (있다면)",
    "location": "위치 정보",
    "phone": "연락처 (있다면)",
    "hours": "영업시간 (있다면)",
    "address": "주소 (있다면)"
  },
  "menu_items": [
    {
      "name": "메뉴/제품명",
      "price": "가격 (있다면)",
      "description": "설명"
    }
  ],
  "features": ["주차가능", "반려동물동반", "키즈존" 등],
  "price_range": "₩|₩₩|₩₩₩ 중 하나 (가격대 표시)",
  "recommended_for": ["데이트", "가족모임", "혼밥" 등],
  "sentiment": "positive|negative|neutral",
  "sentiment_score": -1.0에서 1.0 사이의 실수,
  "summary": "콘텐츠의 상세한 요약 (최소 10문장 이상 작성 필수)",
  "keywords": ["주요 키워드 리스트"],
  "confidence": 0.0에서 1.0 사이의 신뢰도 점수
}

**중요: summary 작성 지침**
- 최소 10문장 이상 작성해야 합니다
- 콘텐츠에서 다룬 모든 주요 주제와 내용을 포함하세요
- 등장하는 모든 인물, 장소, 사건을 구체적으로 언급하세요
- 단순히 요약하지 말고, 내용의 흐름과 맥락을 상세히 설명하세요
- 시청자가 영상을 보지 않아도 전체 내용을 이해할 수 있을 정도로 상세하게 작성하세요

비디오의 시각적 요소, 텍스트, 음성 정보를 모두 활용하여 정확하게 분석해주세요.
JSON 형식만 반환해주세요.
""")

        return "".join(prompt_parts)

    def _parse_classification(self, response_text: str) -> Dict[str, Any]:
        """
        Parse classification response.

        Args:
            response_text: Gemini response text

        Returns:
            Structured classification results
        """
        import json

        try:
            # Remove code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            parsed = json.loads(response_text.strip())
            return parsed

        except json.JSONDecodeError as e:
            # Return default structure if parsing fails
            return {
                "primary_category": "unknown",
                "sub_categories": [],
                "place_info": {},
                "menu_items": [],
                "features": [],
                "price_range": None,
                "recommended_for": [],
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "summary": "",
                "keywords": [],
                "confidence": 0.0,
                "parsing_error": str(e),
                "raw_response": response_text
            }
