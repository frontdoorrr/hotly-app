#!/usr/bin/env python3
"""
AI Category Classification Tests

Tests for validating 80% accuracy requirement for AI-based category classification.
Follows TDD approach for Task 1-2-3: AI 기반 카테고리 분류 시스템 (80% 정확도)
"""

from unittest.mock import patch

from app.models.place import PlaceCategory
from app.services.category_classifier import CategoryClassifier


class TestCategoryClassifier:
    """
    Tests for AI-based category classification system.

    Validates that the classifier meets 80% accuracy requirement
    across various Korean place types.
    """

    def setup_method(self):
        """Setup test data and classifier."""
        self.classifier = CategoryClassifier()

        # Test cases for Korean place classification
        self.test_cases = self._create_classification_test_cases()

    def _create_classification_test_cases(self):
        """Create test cases for category classification validation."""
        return [
            # Restaurant classifications
            {
                "description": "한식당 - 명확한 키워드",
                "place_name": "한옥마을 전통 한정식",
                "place_description": "정통 한국 요리를 제공하는 한정식 전문점",
                "tags": ["한식", "전통음식", "한정식"],
                "expected_category": PlaceCategory.RESTAURANT,
                "min_confidence": 0.85,
            },
            {
                "description": "카페 - 명확한 브랜드명",
                "place_name": "스타벅스 홍대입구역점",
                "place_description": "커피와 디저트를 판매하는 카페",
                "tags": ["커피", "카페", "디저트"],
                "expected_category": PlaceCategory.CAFE,
                "min_confidence": 0.90,
            },
            # Korean-specific business types
            {
                "description": "치킨집 - 한국식 프라이드치킨",
                "place_name": "교촌치킨 홍대점",
                "place_description": "바삭한 프라이드치킨과 맥주를 제공하는 치킨전문점",
                "tags": ["치킨", "맥주", "프라이드치킨"],
                "expected_category": PlaceCategory.RESTAURANT,
                "min_confidence": 0.85,
            },
            {
                "description": "노래방 - 한국식 가라오케",
                "place_name": "코인노래방 24시",
                "place_description": "24시간 운영하는 셀프 노래방",
                "tags": ["노래방", "가라오케", "노래"],
                "expected_category": PlaceCategory.ENTERTAINMENT,
                "min_confidence": 0.90,
            },
            {
                "description": "PC방 - 인터넷 카페",
                "place_name": "와우PC방",
                "place_description": "고사양 컴퓨터로 게임을 즐길 수 있는 PC방",
                "tags": ["PC방", "게임", "인터넷"],
                "expected_category": PlaceCategory.ENTERTAINMENT,
                "min_confidence": 0.85,
            },
            {
                "description": "찜질방 - 한국식 사우나",
                "place_name": "드래곤힐스파",
                "place_description": "24시간 찜질방, 사우나, 휴식공간 제공",
                "tags": ["찜질방", "사우나", "스파", "휴식"],
                "expected_category": PlaceCategory.ENTERTAINMENT,
                "min_confidence": 0.80,
            },
            {
                "description": "분식점 - 한국식 간식",
                "place_name": "이모네 분식",
                "place_description": "떡볶이, 김밥, 튀김 등 분식을 파는 식당",
                "tags": ["분식", "떡볶이", "김밥"],
                "expected_category": PlaceCategory.RESTAURANT,
                "min_confidence": 0.80,
            },
            {
                "description": "포차/술집 - 한국식 선술집",
                "place_name": "홍대포차거리",
                "place_description": "소주와 안주를 파는 한국식 선술집",
                "tags": ["포차", "술집", "소주", "안주"],
                "expected_category": PlaceCategory.BAR,
                "min_confidence": 0.85,
            },
            {
                "description": "관광명소 - 한국 전통문화",
                "place_name": "경복궁",
                "place_description": "조선시대 정궁으로 한국의 대표적인 궁궐",
                "tags": ["궁궐", "관광", "문화재", "역사"],
                "expected_category": PlaceCategory.TOURIST_ATTRACTION,
                "min_confidence": 0.85,
            },
            {
                "description": "쇼핑 - 백화점",
                "place_name": "롯데백화점 본점",
                "place_description": "다양한 브랜드와 상품을 판매하는 대형 백화점",
                "tags": ["쇼핑", "백화점", "브랜드"],
                "expected_category": PlaceCategory.SHOPPING,
                "min_confidence": 0.80,
            },
            {
                "description": "숙박 - 호텔",
                "place_name": "신라호텔 서울",
                "place_description": "5성급 럭셔리 호텔로 최고급 서비스 제공",
                "tags": ["호텔", "숙박", "럭셔리"],
                "expected_category": PlaceCategory.ACCOMMODATION,
                "min_confidence": 0.85,
            },
            {
                "description": "엔터테인먼트 - 영화관",
                "place_name": "CGV 강남점",
                "place_description": "최신 영화를 상영하는 멀티플렉스 영화관",
                "tags": ["영화", "영화관", "엔터테인먼트"],
                "expected_category": PlaceCategory.ENTERTAINMENT,
                "min_confidence": 0.80,
            },
            # Edge cases for accuracy testing
            {
                "description": "모호한 케이스 - 복합 시설",
                "place_name": "홍대 문화공간",
                "place_description": "카페와 갤러리가 함께 있는 복합문화공간",
                "tags": ["문화", "갤러리", "복합시설"],
                "expected_category": PlaceCategory.ENTERTAINMENT,  # 주요 기능 기준
                "min_confidence": 0.60,
            },
        ]

    async def test_category_classification_accuracy_koreanPlaces_meets80PercentTarget(
        self,
    ):
        """
        Test: Category classification achieves 80% accuracy for Korean places

        RED: This test should initially fail until classifier is implemented
        """
        # Given: Korean place test cases
        total_cases = len(self.test_cases)
        correct_predictions = 0

        results = []

        # When: Classify all test cases
        for i, test_case in enumerate(self.test_cases):
            classification_result = await self.classifier.classify_place(
                name=test_case["place_name"],
                description=test_case["place_description"],
                tags=test_case["tags"],
            )

            # Evaluate prediction accuracy
            predicted_category = classification_result.category
            expected_category = test_case["expected_category"]

            is_correct = predicted_category == expected_category

            if is_correct:
                correct_predictions += 1

            # Validate confidence levels for correct predictions
            if is_correct:
                min_confidence = test_case.get("min_confidence", 0.60)
                assert classification_result.confidence >= min_confidence, (
                    f"Case {i}: {test_case['description']} - "
                    f"Confidence {classification_result.confidence:.3f} below minimum {min_confidence}"
                )

            results.append(
                {
                    "case": i,
                    "description": test_case["description"],
                    "predicted": predicted_category,
                    "expected": expected_category,
                    "confidence": classification_result.confidence,
                    "correct": is_correct,
                }
            )

        # Then: Accuracy should meet 80% target
        accuracy = correct_predictions / total_cases

        print("\n📊 Category Classification Accuracy Results:")
        print(f"   Total test cases: {total_cases}")
        print(f"   Correct predictions: {correct_predictions}")
        print(f"   Accuracy: {accuracy:.1%}")
        print("   Target: 80%")

        for result in results:
            status = "✅" if result["correct"] else "❌"
            print(
                f"   {status} Case {result['case']}: {result['description']} "
                f"(predicted: {result['predicted']}, confidence: {result['confidence']:.3f})"
            )

        assert (
            accuracy >= 0.80
        ), f"Category classification accuracy {accuracy:.1%} below 80% target"

    async def test_restaurant_classification_koreanCuisine_highAccuracy(self):
        """
        Test: Korean restaurant types are classified with high accuracy

        Focus on Korean-specific food categories
        """
        # Given: Korean restaurant test cases
        korean_restaurants = [
            (
                "한솥도시락",
                "한식 도시락 전문점",
                ["한식", "도시락"],
                PlaceCategory.RESTAURANT,
            ),
            (
                "김치찌개집",
                "김치찌개와 한식을 파는 식당",
                ["한식", "찌개"],
                PlaceCategory.RESTAURANT,
            ),
            (
                "삼겹살 구이집",
                "삼겹살과 고기구이 전문",
                ["고기", "구이", "삼겹살"],
                PlaceCategory.RESTAURANT,
            ),
            (
                "치킨집",
                "치킨과 맥주를 파는 치킨전문점",
                ["치킨", "맥주"],
                PlaceCategory.RESTAURANT,
            ),
        ]

        # When: Classify each restaurant
        for name, description, tags, expected in korean_restaurants:
            result = await self.classifier.classify_place(name, description, tags)

            # Then: Should correctly classify as restaurant
            assert (
                result.category == expected
            ), f"Failed to classify '{name}' as restaurant (got: {result.category})"
            assert (
                result.confidence >= 0.70
            ), f"Low confidence for '{name}': {result.confidence:.3f}"

    async def test_cafe_vs_restaurant_distinction_ambiguousCases_correctClassification(
        self,
    ):
        """
        Test: Classifier distinguishes between cafes and restaurants in ambiguous cases

        Important for Korean dining culture where boundaries can be unclear
        """
        # Given: Ambiguous cafe/restaurant cases
        ambiguous_cases = [
            (
                "브런치 카페",
                "브런치와 커피를 제공하는 카페",
                ["브런치", "커피"],
                PlaceCategory.CAFE,
            ),
            (
                "디저트 카페",
                "케이크와 디저트를 파는 카페",
                ["디저트", "케이크"],
                PlaceCategory.CAFE,
            ),
            (
                "파스타 전문점",
                "파스타와 이탈리안 요리 전문",
                ["파스타", "이탈리안"],
                PlaceCategory.RESTAURANT,
            ),
            (
                "피자집",
                "피자와 음료를 파는 식당",
                ["피자", "음식"],
                PlaceCategory.RESTAURANT,
            ),
        ]

        # When & Then: Each case should be classified correctly
        for name, description, tags, expected in ambiguous_cases:
            result = await self.classifier.classify_place(name, description, tags)

            assert (
                result.category == expected
            ), f"Misclassified '{name}': expected {expected}, got {result.category}"

    async def test_korean_entertainment_classification_uniqueTypes_correctCategories(
        self,
    ):
        """
        Test: Korean-specific entertainment venues are classified correctly

        Tests uniquely Korean entertainment types
        """
        # Given: Korean entertainment venues
        korean_entertainment = [
            (
                "노래방",
                "가족과 친구들이 노래를 부르는 곳",
                ["노래", "가라오케"],
                PlaceCategory.ENTERTAINMENT,
            ),
            (
                "PC방",
                "컴퓨터 게임을 할 수 있는 곳",
                ["게임", "컴퓨터"],
                PlaceCategory.ENTERTAINMENT,
            ),
            (
                "찜질방",
                "사우나와 휴식을 제공하는 시설",
                ["사우나", "휴식", "찜질"],
                PlaceCategory.ENTERTAINMENT,
            ),
            (
                "볼링장",
                "볼링을 칠 수 있는 스포츠 시설",
                ["볼링", "스포츠"],
                PlaceCategory.ENTERTAINMENT,
            ),
        ]

        # When & Then: Should classify as entertainment
        for name, description, tags, expected in korean_entertainment:
            result = await self.classifier.classify_place(name, description, tags)

            assert (
                result.category == expected
            ), f"Failed to classify '{name}' as entertainment (got: {result.category})"

    @patch("app.services.ai.gemini_analyzer.GeminiAnalyzer.analyze_content")
    async def test_ai_integration_geminiAnalyzer_properIntegration(self, mock_analyze):
        """
        Test: Category classifier integrates properly with Gemini AI

        GREEN: Test AI integration without requiring actual API calls
        """
        # Given: Mock AI response
        mock_analyze.return_value = {
            "category": "RESTAURANT",
            "confidence": 0.85,
            "reasoning": "Korean traditional restaurant serving hansik",
        }

        # When: Classify with AI
        result = await self.classifier.classify_place("한정식집", "전통 한국요리", ["한식", "전통"])

        # Then: Should use AI results properly
        assert result.category == PlaceCategory.RESTAURANT
        assert result.confidence == 0.85
        mock_analyze.assert_called_once()

    async def test_confidence_calibration_variousInputs_appropriateConfidence(self):
        """
        Test: Confidence scores are properly calibrated for different input qualities

        Ensures confidence reflects actual prediction reliability
        """
        # Given: Inputs with varying clarity
        test_inputs = [
            ("스타벅스", "커피전문점", ["커피"], 0.90),  # Very clear
            ("음식점", "음식을 파는 곳", ["음식"], 0.60),  # Vague
            ("복합문화공간", "다양한 활동", ["문화"], 0.50),  # Ambiguous
        ]

        # When & Then: Confidence should reflect input clarity
        for name, description, tags, min_confidence in test_inputs:
            result = await self.classifier.classify_place(name, description, tags)

            assert (
                result.confidence >= min_confidence
            ), f"Confidence too low for '{name}': {result.confidence:.3f} < {min_confidence}"
