#!/usr/bin/env python3
"""
Duplicate Detection Accuracy Tests

Tests for validating 95% accuracy requirement for duplicate detection algorithm.
Follows TDD approach for Task 1-2-2: 중복 방지 알고리즘 구현 (95% 정확도)
"""

from app.schemas.place import PlaceCreate
from app.services.duplicate_detector import DuplicateDetector


class TestDuplicateDetectorAccuracy:
    """
    Accuracy tests for duplicate detection algorithm.

    Validates that the algorithm meets 95% accuracy requirement
    across various real-world scenarios.
    """

    def setup_method(self):
        """Setup test data and detector."""
        self.detector = DuplicateDetector()

        # Test data representing real-world scenarios
        self.test_cases = self._create_accuracy_test_cases()

    def _create_accuracy_test_cases(self):
        """Create comprehensive test cases for accuracy validation."""
        return [
            # Exact duplicates (should detect with 100% confidence)
            {
                "description": "정확한 중복 - 이름과 주소 동일",
                "new_place": PlaceCreate(
                    name="스타벅스 홍대입구역점",
                    address="서울특별시 마포구 홍익로 69",
                    latitude=37.5572,
                    longitude=126.9238,
                ),
                "existing_place": PlaceCreate(
                    name="스타벅스 홍대입구역점",
                    address="서울특별시 마포구 홍익로 69",
                    latitude=37.5572,
                    longitude=126.9238,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.95,
            },
            # Near duplicates with slight variations (should detect)
            {
                "description": "유사 중복 - 띄어쓰기 차이",
                "new_place": PlaceCreate(
                    name="스타벅스홍대입구역점",
                    address="서울특별시 마포구 홍익로69",
                    latitude=37.5572,
                    longitude=126.9238,
                ),
                "existing_place": PlaceCreate(
                    name="스타벅스 홍대입구역점",
                    address="서울특별시 마포구 홍익로 69",
                    latitude=37.5572,
                    longitude=126.9238,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.85,
            },
            # Korean place name variations - testing algorithm robustness
            {
                "description": "한글 변형 - XX점 vs XX지점",
                "new_place": PlaceCreate(
                    name="투썸플레이스 홍대점",
                    address="서울특별시 마포구 홍익로 72",
                    latitude=37.5573,
                    longitude=126.9240,
                ),
                "existing_place": PlaceCreate(
                    name="투썸플레이스 홍대지점",
                    address="서울특별시 마포구 홍익로 72",
                    latitude=37.5573,
                    longitude=126.9240,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.85,
            },
            {
                "description": "영어 표기 차이 - 한글 vs 영어명",
                "new_place": PlaceCreate(
                    name="KFC 강남점",
                    address="서울특별시 강남구 강남대로 396",
                    latitude=37.4980,
                    longitude=127.0278,
                ),
                "existing_place": PlaceCreate(
                    name="케이에프씨 강남점",
                    address="서울특별시 강남구 강남대로 396",
                    latitude=37.4980,
                    longitude=127.0278,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.70,
            },
            {
                "description": "주소 축약형 - 정식주소 vs 축약주소",
                "new_place": PlaceCreate(
                    name="버거킹 명동점",
                    address="서울시 중구 명동길 14",
                    latitude=37.5636,
                    longitude=126.9834,
                ),
                "existing_place": PlaceCreate(
                    name="버거킹 명동점",
                    address="서울특별시 중구 명동길 14",
                    latitude=37.5636,
                    longitude=126.9834,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.90,
            },
            {
                "description": "한글 브랜드명 변형 - 띄어쓰기와 표기 차이",
                "new_place": PlaceCreate(
                    name="파리바게뜨 이대점",
                    address="서울특별시 서대문구 이화여대길 52",
                    latitude=37.5563,
                    longitude=126.9468,
                ),
                "existing_place": PlaceCreate(
                    name="파리바게트 이대점",
                    address="서울특별시 서대문구 이화여대길 52",
                    latitude=37.5563,
                    longitude=126.9468,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.85,
            },
            # Geographical proximity with similar names (should detect)
            {
                "description": "지리적 근접성 - 같은 브랜드 다른 지점",
                "new_place": PlaceCreate(
                    name="맥도날드 홍대점",
                    address="서울특별시 마포구 홍익로 65",
                    latitude=37.5570,
                    longitude=126.9240,
                ),
                "existing_place": PlaceCreate(
                    name="맥도날드 홍대입구점",
                    address="서울특별시 마포구 홍익로 71",
                    latitude=37.5574,
                    longitude=126.9236,
                ),
                "expected_duplicate": True,
                "min_confidence": 0.70,
            },
            # False positives to avoid (should NOT detect as duplicates)
            {
                "description": "다른 장소 - 같은 브랜드 다른 지역",
                "new_place": PlaceCreate(
                    name="스타벅스 강남역점",
                    address="서울특별시 강남구 강남대로 390",
                    latitude=37.4979,
                    longitude=127.0276,
                ),
                "existing_place": PlaceCreate(
                    name="스타벅스 홍대입구역점",
                    address="서울특별시 마포구 홍익로 69",
                    latitude=37.5572,
                    longitude=126.9238,
                ),
                "expected_duplicate": False,
                "max_confidence": 0.60,
            },
            # Edge case: Similar names but different categories
            {
                "description": "다른 장소 - 유사한 이름 다른 업종",
                "new_place": PlaceCreate(
                    name="홍대카페",
                    address="서울특별시 마포구 홍익로 100",
                    latitude=37.5580,
                    longitude=126.9250,
                ),
                "existing_place": PlaceCreate(
                    name="홍대카페거리",
                    address="서울특별시 마포구 홍익로 50",
                    latitude=37.5565,
                    longitude=126.9230,
                ),
                "expected_duplicate": False,
                "max_confidence": 0.65,
            },
        ]

    def test_duplicate_detection_accuracy_comprehensiveScenarios_meets95PercentTarget(
        self,
    ):
        """
        Test: Duplicate detection achieves 95% accuracy across test scenarios

        RED: This test should initially validate current accuracy levels
        """
        # Given: Comprehensive test scenarios
        total_cases = len(self.test_cases)
        correct_predictions = 0

        results = []

        # When: Run detection on all test cases
        for i, test_case in enumerate(self.test_cases):
            result = self.detector._check_all_methods(
                test_case["new_place"], test_case["existing_place"]
            )

            # Evaluate prediction accuracy
            predicted_duplicate = result.confidence >= 0.65  # Default threshold
            expected_duplicate = test_case["expected_duplicate"]

            is_correct = predicted_duplicate == expected_duplicate

            if is_correct:
                correct_predictions += 1

            # Validate confidence levels for correct predictions
            if expected_duplicate and predicted_duplicate:
                min_confidence = test_case.get("min_confidence", 0.65)
                assert result.confidence >= min_confidence, (
                    f"Case {i}: {test_case['description']} - "
                    f"Confidence {result.confidence:.3f} below minimum {min_confidence}"
                )

            if not expected_duplicate and not predicted_duplicate:
                max_confidence = test_case.get("max_confidence", 0.65)
                assert result.confidence <= max_confidence, (
                    f"Case {i}: {test_case['description']} - "
                    f"Confidence {result.confidence:.3f} above maximum {max_confidence}"
                )

            results.append(
                {
                    "case": i,
                    "description": test_case["description"],
                    "predicted": predicted_duplicate,
                    "expected": expected_duplicate,
                    "confidence": result.confidence,
                    "correct": is_correct,
                }
            )

        # Then: Accuracy should meet 95% target
        accuracy = correct_predictions / total_cases

        print("\n📊 Duplicate Detection Accuracy Results:")
        print(f"   Total test cases: {total_cases}")
        print(f"   Correct predictions: {correct_predictions}")
        print(f"   Accuracy: {accuracy:.1%}")
        print("   Target: 95%")

        for result in results:
            status = "✅" if result["correct"] else "❌"
            print(
                f"   {status} Case {result['case']}: {result['description']} "
                f"(confidence: {result['confidence']:.3f})"
            )

        assert (
            accuracy >= 0.95
        ), f"Duplicate detection accuracy {accuracy:.1%} below 95% target"

    def test_exact_match_detection_identicalPlaces_perfectAccuracy(self):
        """
        Test: Exact matches are detected with perfect accuracy

        GREEN: This should pass with current implementation
        """
        # Given: Identical places
        place = PlaceCreate(
            name="테스트 카페",
            address="서울특별시 강남구 테스트로 123",
            latitude=37.5000,
            longitude=127.0000,
        )

        # When: Check for exact match
        result = self.detector._check_exact_match(place, place)

        # Then: Should detect as duplicate with perfect confidence
        assert result.is_duplicate is True
        assert result.confidence == 1.0
        assert result.match_type == "exact"

    def test_geographical_threshold_adjustment_varyingDistances_optimalDetection(self):
        """
        Test: Geographical threshold provides optimal detection rates

        This test validates the 50-meter threshold for geographical proximity
        """
        # Given: Places at various distances
        base_place = PlaceCreate(
            name="기준 카페",
            address="서울특별시 강남구 테스트로 100",
            latitude=37.5000,
            longitude=127.0000,
        )

        test_distances = [
            (10, True, "매우 가까운 거리 - 중복으로 판단해야"),
            (25, True, "가까운 거리 - 중복으로 판단해야"),
            (49, True, "임계값 내 - 중복으로 판단해야"),
            (51, False, "임계값 밖 - 중복이 아님"),
            (100, False, "먼 거리 - 중복이 아님"),
            (500, False, "매우 먼 거리 - 중복이 아님"),
        ]

        for distance_m, should_detect, description in test_distances:
            # Calculate coordinates for specific distance
            # Approximate: 1 degree ≈ 111km, so for small distances:
            lat_offset = distance_m / 111000

            nearby_place = PlaceCreate(
                name="기준 카페",  # Same name for geo proximity test
                address="서울특별시 강남구 테스트로 101",
                latitude=base_place.latitude + lat_offset,
                longitude=base_place.longitude,
            )

            # When: Check geographical proximity
            result = self.detector._check_geographical_proximity(
                base_place, nearby_place
            )

            # Then: Should detect appropriately based on distance
            if should_detect:
                assert (
                    result.is_duplicate is True
                ), f"{description} (distance: {distance_m}m)"
                assert (
                    result.confidence > 0.65
                ), f"Low confidence for {description}: {result.confidence:.3f}"
            else:
                assert (
                    result.is_duplicate is False
                ), f"{description} (distance: {distance_m}m)"

    def test_korean_text_normalization_variousFormats_consistentResults(self):
        """
        Test: Korean text normalization handles various formats consistently

        Critical for Korean place names and addresses
        """
        # Given: Various Korean text formats
        test_normalizations = [
            ("스타벅스", "스타벅스", "기본 한글"),
            ("스타 벅스", "스타벅스", "띄어쓰기 제거"),
            ("Starbucks", "starbucks", "영어 소문자 변환"),
            ("스타벅스!", "스타벅스", "특수문자 제거"),
            ("서울특별시", "서울", "주소 정규화"),
            ("서울시", "서울", "축약형 정규화"),
        ]

        for input_text, expected, description in test_normalizations:
            # When: Normalize text
            if "주소" in description:
                result = self.detector._normalize_address(input_text)
            else:
                result = self.detector._normalize_name(input_text)

            # Then: Should produce expected normalized form
            assert (
                result == expected
            ), f"{description}: '{input_text}' → '{result}' (expected: '{expected}')"

    def _check_all_methods(self, new_place: PlaceCreate, existing_place: PlaceCreate):
        """Helper method to test all detection methods and return best result."""
        methods = [
            self.detector._check_exact_match,
            self.detector._check_name_similarity,
            self.detector._check_address_similarity,
            self.detector._check_geographical_proximity,
        ]

        best_result = None
        for method in methods:
            try:
                result = method(new_place, existing_place)
                if best_result is None or result.confidence > best_result.confidence:
                    best_result = result
            except Exception as e:
                # Log the exception for debugging
                print(f"Method {method.__name__} failed: {e}")
                continue

        return best_result or self.detector._check_exact_match(
            new_place, existing_place
        )


# Extension method for the DuplicateDetector class
def _check_all_methods(self, new_place: PlaceCreate, existing_place: PlaceCreate):
    """Helper method for testing - check all detection methods."""
    methods = [
        self._check_exact_match,
        self._check_name_similarity,
        self._check_address_similarity,
        self._check_geographical_proximity,
    ]

    best_result = None
    for method in methods:
        try:
            result = method(new_place, existing_place)
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result
        except Exception as e:
            # Log the exception for debugging
            print(f"Method {method.__name__} failed: {e}")
            continue

    return best_result


# Monkey patch for testing
DuplicateDetector._check_all_methods = _check_all_methods
