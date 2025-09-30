"""
AI-based Category Classification Service

Provides automated place category classification using Gemini AI.
Implements Task 1-2-3: AI 기반 카테고리 분류 시스템 (80% 정확도)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models.place import PlaceCategory
from app.services.ai.gemini_analyzer import GeminiAnalyzer


@dataclass
class ClassificationResult:
    """Result of category classification."""

    category: PlaceCategory
    confidence: float
    reasoning: Optional[str] = None
    alternative_categories: Optional[List[PlaceCategory]] = None


class CategoryClassifier:
    """
    AI-based category classification system for Korean places.

    Uses Gemini AI combined with rule-based classification
    to achieve 80%+ accuracy for Korean business types.
    """

    def __init__(self):
        """Initialize category classifier."""
        self.gemini_analyzer = GeminiAnalyzer()

        # Korean-specific keywords for rule-based classification
        self.category_keywords = {
            PlaceCategory.RESTAURANT: [
                "식당",
                "맛집",
                "요리",
                "음식",
                "한식",
                "중식",
                "일식",
                "양식",
                "치킨",
                "피자",
                "파스타",
                "분식",
                "떡볶이",
                "김밥",
                "국수",
                "고기",
                "삼겹살",
                "갈비",
                "불고기",
                "비빔밥",
                "냉면",
            ],
            PlaceCategory.CAFE: [
                "카페",
                "커피",
                "coffee",
                "스타벅스",
                "이디야",
                "카페베네",
                "디저트",
                "케이크",
                "브런치",
                "라떼",
                "아메리카노",
                "차",
                "베이커리",
                "빵집",
            ],
            PlaceCategory.BAR: [
                "술집",
                "바",
                "bar",
                "pub",
                "맥주",
                "소주",
                "위스키",
                "와인",
                "포차",
                "호프",
                "칵테일",
                "안주",
                "이자카야",
                "브루어리",
            ],
            PlaceCategory.TOURIST_ATTRACTION: [
                "궁궐",
                "박물관",
                "미술관",
                "관광",
                "명소",
                "문화재",
                "유적지",
                "공원",
                "전망대",
                "타워",
                "경복궁",
                "창덕궁",
                "남산",
                "한강",
                "체험관",
                "전시관",
                "역사",
                "전통",
            ],
            PlaceCategory.SHOPPING: [
                "쇼핑",
                "백화점",
                "마트",
                "쇼핑몰",
                "아울렛",
                "시장",
                "상가",
                "롯데",
                "현대",
                "신세계",
                "이마트",
                "홈플러스",
                "코스트코",
                "브랜드",
                "의류",
                "패션",
                "액세서리",
            ],
            PlaceCategory.ACCOMMODATION: [
                "호텔",
                "모텔",
                "펜션",
                "리조트",
                "게스트하우스",
                "숙박",
                "accommodation",
                "hotel",
                "resort",
                "stay",
                "힐튼",
                "신라",
                "롯데호텔",
                "하얏트",
                "메리어트",
            ],
            PlaceCategory.ENTERTAINMENT: [
                "노래방",
                "PC방",
                "찜질방",
                "영화관",
                "놀이공원",
                "볼링장",
                "당구장",
                "오락실",
                "게임",
                "카라오케",
                "사우나",
                "스파",
                "클럽",
                "디스코",
                "극장",
                "공연장",
                "콘서트홀",
            ],
        }

    async def classify_place(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ClassificationResult:
        """
        Classify place category using hybrid AI + rule-based approach.

        Args:
            name: Place name
            description: Place description (optional)
            tags: Place tags (optional)

        Returns:
            ClassificationResult with category, confidence, and reasoning
        """
        # Stage 1: Rule-based classification for high-confidence cases
        rule_result = self._classify_with_rules(name, description, tags)

        if rule_result.confidence >= 0.85:
            return rule_result

        # Stage 2: AI-based classification for complex cases
        ai_result = await self._classify_with_ai(name, description, tags)

        # Stage 3: Combine results for final decision
        final_result = self._combine_results(rule_result, ai_result)

        return final_result

    def _classify_with_rules(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ClassificationResult:
        """Rule-based classification using Korean keywords."""

        # Combine all text for analysis
        text_content = " ".join(
            filter(None, [name or "", description or "", " ".join(tags or [])])
        ).lower()

        category_scores = {}

        # Calculate keyword match scores for each category
        for category, keywords in self.category_keywords.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword in text_content:
                    # Weight by keyword specificity and length
                    weight = len(keyword) / 10.0 + 1.0
                    score += weight
                    matched_keywords.append(keyword)

            if score > 0:
                category_scores[category] = {
                    "score": score,
                    "keywords": matched_keywords,
                }

        if not category_scores:
            return ClassificationResult(
                category=PlaceCategory.OTHER,
                confidence=0.1,
                reasoning="No matching keywords found",
            )

        # Find best category
        best_category = max(
            category_scores.keys(), key=lambda c: category_scores[c]["score"]
        )
        best_score = category_scores[best_category]["score"]
        matched_keywords = category_scores[best_category]["keywords"]

        # Normalize confidence (0.0 to 1.0)
        max_possible_score = len(self.category_keywords[best_category]) * 2.0
        confidence = min(0.95, best_score / max_possible_score)

        # Boost confidence for very specific keywords
        if any(keyword in ["치킨", "노래방", "PC방", "찜질방"] for keyword in matched_keywords):
            confidence = min(0.95, confidence + 0.2)

        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            reasoning=f"Matched keywords: {', '.join(matched_keywords[:3])}",
        )

    async def _classify_with_ai(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ClassificationResult:
        """AI-based classification using Gemini."""

        # Prepare content for AI analysis
        content_parts = [f"장소명: {name}"]

        if description:
            content_parts.append(f"설명: {description}")

        if tags:
            content_parts.append(f"태그: {', '.join(tags)}")

        content = "\n".join(content_parts)

        # Create AI prompt for category classification
        prompt = f"""
다음 한국 장소의 카테고리를 분류해주세요.

{content}

분류 가능한 카테고리:
- RESTAURANT: 식당, 음식점 (한식, 중식, 일식, 양식, 치킨, 분식 등)
- CAFE: 카페, 커피숍, 디저트 전문점
- BAR: 술집, 바, 포차, 호프집
- TOURIST_ATTRACTION: 관광명소, 궁궐, 박물관, 공원
- SHOPPING: 쇼핑몰, 백화점, 마트, 시장
- ACCOMMODATION: 호텔, 모텔, 펜션, 숙박시설
- ENTERTAINMENT: 노래방, PC방, 찜질방, 영화관, 놀이시설
- OTHER: 기타

응답 형식:
{{
    "category": "선택된_카테고리",
    "confidence": 0.85,
    "reasoning": "분류 근거"
}}
        """

        try:
            # Get AI analysis
            ai_response = await self.gemini_analyzer.analyze_content(
                content=prompt, analysis_type="category_classification"
            )

            # Parse AI response
            if isinstance(ai_response, dict):
                category_str = ai_response.get("category", "OTHER")
                confidence = float(ai_response.get("confidence", 0.5))
                reasoning = ai_response.get("reasoning", "AI classification")

                # Convert string to PlaceCategory enum
                try:
                    category = PlaceCategory(category_str.lower())
                except ValueError:
                    category = PlaceCategory.OTHER
                    confidence = 0.3

                return ClassificationResult(
                    category=category,
                    confidence=min(0.95, confidence),
                    reasoning=reasoning,
                )

        except Exception as e:
            # Fallback on AI failure - log the error for debugging
            print(f"AI classification failed: {e}")
            pass

        # Default fallback
        return ClassificationResult(
            category=PlaceCategory.OTHER,
            confidence=0.3,
            reasoning="AI classification failed, using fallback",
        )

    def _combine_results(
        self, rule_result: ClassificationResult, ai_result: ClassificationResult
    ) -> ClassificationResult:
        """Combine rule-based and AI results for final classification."""

        # If both agree on category, boost confidence
        if rule_result.category == ai_result.category:
            combined_confidence = min(
                0.95, (rule_result.confidence + ai_result.confidence) / 2 + 0.1
            )

            return ClassificationResult(
                category=rule_result.category,
                confidence=combined_confidence,
                reasoning=f"Rule + AI agreement: {rule_result.reasoning}",
            )

        # If they disagree, choose the higher confidence result
        if rule_result.confidence > ai_result.confidence:
            return rule_result
        else:
            return ai_result

    def get_category_keywords(self, category: PlaceCategory) -> List[str]:
        """Get keywords associated with a specific category."""
        return self.category_keywords.get(category, [])

    def analyze_classification_confidence(
        self, name: str, description: Optional[str] = None
    ) -> Dict[PlaceCategory, float]:
        """
        Analyze confidence scores for all categories.

        Useful for debugging and understanding classification decisions.
        """
        text_content = " ".join(filter(None, [name or "", description or ""])).lower()

        confidence_scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_content:
                    score += len(keyword) / 10.0 + 1.0

            max_possible = len(keywords) * 2.0
            confidence_scores[category] = (
                min(0.95, score / max_possible) if max_possible > 0 else 0.0
            )

        return confidence_scores
