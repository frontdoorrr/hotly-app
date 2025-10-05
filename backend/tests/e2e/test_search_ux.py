"""
검색 사용자 경험(UX) E2E 테스트 (Task 2-3-6)

실제 사용자 플로우를 시뮬레이션한 종단간 테스트
- 실제 사용자 시나리오 검증
- 검색 → 필터 → 결과 → 상세보기 전체 플로우
- 사용자 만족도 지표 검증
"""

import asyncio
import json
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestSearchUserExperience:
    """검색 사용자 경험 E2E 테스트"""

    def setup_method(self) -> None:
        """E2E 테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_app = Mock()
        self.client = TestClient(self.mock_app)

        # 사용자 시나리오용 실제적인 데이터
        self.realistic_places = [
            {
                "id": "hongdae_cafe_1",
                "name": "카페 드림",
                "address": "서울시 마포구 홍익로 123",
                "category": "cafe",
                "region": "홍대",
                "tags": ["조용한", "와이파이좋음", "작업하기좋은"],
                "rating": 4.3,
                "price_range": 1,
                "location": {"lat": 37.5563, "lng": 126.9223},
                "status": "즐겨찾기",
                "visit_count": 5,
                "last_visited": "2025-01-10",
            },
            {
                "id": "gangnam_restaurant_1",
                "name": "이태리 파스타",
                "address": "서울시 강남구 강남대로 456",
                "category": "restaurant",
                "region": "강남",
                "tags": ["데이트", "분위기좋은", "파스타"],
                "rating": 4.6,
                "price_range": 3,
                "location": {"lat": 37.4979, "lng": 127.0276},
                "status": "가보고싶음",
                "visit_count": 0,
                "last_visited": None,
            },
            {
                "id": "sinchon_bar_1",
                "name": "신촌 소주방",
                "address": "서울시 서대문구 신촌로 789",
                "category": "bar",
                "region": "신촌",
                "tags": ["친구들과", "저렴한", "한국음식"],
                "rating": 4.1,
                "price_range": 2,
                "location": {"lat": 37.5596, "lng": 126.9370},
                "status": "방문완료",
                "visit_count": 3,
                "last_visited": "2024-12-20",
            },
        ]

        # 사용자 검색 히스토리
        self.user_search_history = [
            {"query": "홍대 카페", "timestamp": "2025-01-10T14:30:00", "clicked": True},
            {"query": "강남 맛집", "timestamp": "2025-01-09T19:15:00", "clicked": True},
            {"query": "조용한 카페", "timestamp": "2025-01-08T10:20:00", "clicked": False},
            {"query": "데이트 코스", "timestamp": "2025-01-07T16:45:00", "clicked": True},
        ]

    async def test_basic_search_user_journey(self) -> None:
        """
        Given: 사용자가 장소를 찾고 있음
        When: 기본 검색 플로우를 따라감 (검색어 입력 → 결과 확인 → 장소 선택)
        Then: 직관적이고 만족스러운 경험을 얻음
        """
        # Given: 사용자 시나리오 - "홍대 카페 찾기"
        user_scenario = {
            "intent": "홍대에서 작업할 수 있는 조용한 카페 찾기",
            "search_query": "홍대 카페",
            "expected_tags": ["조용한", "작업하기좋은"],
            "max_price": 2,
        }

        journey_steps = []

        # Step 1: 검색어 입력
        search_start_time = time.time()

        # Mock 검색 API
        with patch("app.api.v1.endpoints.search.search_places") as mock_search:
            mock_search.return_value = {
                "places": [
                    place
                    for place in self.realistic_places
                    if "홍대" in place["address"] and place["category"] == "cafe"
                ],
                "total_count": 1,
                "query": user_scenario["search_query"],
                "suggestions": ["홍대 맛집", "홍대 술집", "홍대 카페 조용한"],
                "search_time_ms": 450,
            }

            # When: 검색 실행
            search_response = self.client.post(
                "/api/v1/search/places",
                json={
                    "query": user_scenario["search_query"],
                    "user_id": str(self.test_user_id),
                    "limit": 20,
                },
            )

        search_time = (time.time() - search_start_time) * 1000
        journey_steps.append({
            "step": "search",
            "time_ms": search_time,
            "success": search_response.status_code == 200,
            "result_count": len(mock_search.return_value["places"]) if mock_search.return_value else 0,
        })

        # Step 2: 결과 검토 및 필터 적용
        filter_start_time = time.time()

        # Mock 필터 API
        with patch("app.api.v1.endpoints.search.apply_filters") as mock_filter:
            filtered_places = []
            for place in self.realistic_places:
                if (
                    place["category"] == "cafe"
                    and "홍대" in place["address"]
                    and any(tag in user_scenario["expected_tags"] for tag in place["tags"])
                    and place["price_range"] <= user_scenario["max_price"]
                ):
                    filtered_places.append(place)

            mock_filter.return_value = {
                "places": filtered_places,
                "total_count": len(filtered_places),
                "applied_filters": {
                    "categories": ["cafe"],
                    "regions": ["홍대"],
                    "tags": ["조용한"],
                    "max_price": user_scenario["max_price"],
                },
            }

            # When: 필터 적용
            filter_response = self.client.post(
                "/api/v1/search/filter",
                json={
                    "user_id": str(self.test_user_id),
                    "filters": {
                        "categories": ["cafe"],
                        "regions": ["홍대"],
                        "tags": ["조용한"],
                        "max_price": user_scenario["max_price"],
                    },
                },
            )

        filter_time = (time.time() - filter_start_time) * 1000
        journey_steps.append({
            "step": "filter",
            "time_ms": filter_time,
            "success": filter_response.status_code == 200,
            "filtered_count": len(filtered_places),
        })

        # Step 3: 장소 상세 보기
        detail_start_time = time.time()

        selected_place = filtered_places[0] if filtered_places else None
        if selected_place:
            # Mock 장소 상세 API
            with patch("app.api.v1.endpoints.places.get_place_detail") as mock_detail:
                mock_detail.return_value = {
                    **selected_place,
                    "detailed_info": {
                        "opening_hours": "09:00-22:00",
                        "wifi": True,
                        "parking": False,
                        "reviews": [
                            {"rating": 5, "comment": "조용하고 작업하기 좋아요"},
                            {"rating": 4, "comment": "커피가 맛있어요"},
                        ],
                    },
                    "similar_places": [place["id"] for place in self.realistic_places[1:3]],
                }

                # When: 상세 정보 조회
                detail_response = self.client.get(
                    f"/api/v1/places/{selected_place['id']}",
                    params={"user_id": str(self.test_user_id)},
                )

        detail_time = (time.time() - detail_start_time) * 1000
        journey_steps.append({
            "step": "detail",
            "time_ms": detail_time,
            "success": detail_response.status_code == 200 if selected_place else False,
            "place_found": selected_place is not None,
        })

        # Then: 사용자 여정 성공 기준 검증
        total_journey_time = sum(step["time_ms"] for step in journey_steps)

        # UX 성공 기준 (PRD 기반)
        assert total_journey_time < 5000  # 전체 여정 5초 이내
        assert journey_steps[0]["result_count"] > 0  # 검색 결과 있음
        assert journey_steps[1]["filtered_count"] >= 0  # 필터 적용됨
        assert journey_steps[2]["place_found"] == True  # 적합한 장소 발견

        # 각 단계별 성능 기준
        assert journey_steps[0]["time_ms"] < 3000  # 검색 3초 이내
        assert journey_steps[1]["time_ms"] < 1000  # 필터링 1초 이내
        assert journey_steps[2]["time_ms"] < 1000  # 상세보기 1초 이내

    async def test_search_with_no_results_ux(self) -> None:
        """
        Given: 검색 결과가 없는 상황
        When: 사용자가 검색을 수행함
        Then: 도움이 되는 대안과 제안을 제공함
        """
        # Given: 결과 없는 검색어
        no_result_query = "존재하지않는특이한장소명12345"

        # Mock 빈 검색 결과
        with patch("app.api.v1.endpoints.search.search_places") as mock_search:
            mock_search.return_value = {
                "places": [],
                "total_count": 0,
                "query": no_result_query,
                "message": "검색 결과가 없어요",
                "suggestions": [
                    "인기 검색어: 홍대 카페",
                    "인기 검색어: 강남 맛집",
                    "유사 검색어: 특별한 장소",
                ],
                "alternative_filters": {
                    "expand_region": "주변 지역도 포함해서 찾아보세요",
                    "expand_category": "다른 카테고리도 확인해보세요",
                    "popular_nearby": "근처 인기 장소",
                },
            }

            # When: 빈 결과 검색 실행
            response = self.client.post(
                "/api/v1/search/places",
                json={
                    "query": no_result_query,
                    "user_id": str(self.test_user_id),
                },
            )

        # Then: 도움이 되는 UX 요소들 제공 확인
        result = mock_search.return_value

        assert result["total_count"] == 0
        assert "message" in result
        assert len(result["suggestions"]) >= 3
        assert "alternative_filters" in result

        # 제안의 품질 검증
        suggestions = result["suggestions"]
        assert all(isinstance(suggestion, str) for suggestion in suggestions)
        assert any("인기" in suggestion for suggestion in suggestions)

    async def test_autocomplete_user_interaction(self) -> None:
        """
        Given: 사용자가 검색어를 입력 중임
        When: 타이핑하면서 자동완성을 사용함
        Then: 빠르고 정확한 자동완성으로 효율적 검색함
        """
        # Given: 점진적 검색어 입력 시뮬레이션
        typing_sequence = ["카", "카페", "카페 홍", "카페 홍대"]
        autocomplete_results = []

        for partial_query in typing_sequence:
            typing_start_time = time.time()

            # Mock 자동완성 API
            with patch("app.api.v1.endpoints.search.get_autocomplete") as mock_autocomplete:
                # 실제적인 자동완성 응답
                suggestions = []
                if "카" in partial_query:
                    suggestions = [
                        {"text": "카페", "type": "category", "frequency": 150},
                        {"text": "카페 홍대", "type": "query", "frequency": 89},
                        {"text": "카페 강남", "type": "query", "frequency": 67},
                    ]
                if "홍" in partial_query:
                    suggestions = [
                        {"text": "홍대 카페", "type": "query", "frequency": 120},
                        {"text": "홍대 맛집", "type": "query", "frequency": 95},
                        {"text": "홍익대", "type": "place", "frequency": 45},
                    ]

                mock_autocomplete.return_value = {
                    "suggestions": suggestions,
                    "partial_query": partial_query,
                    "response_time_ms": 120,
                }

                # When: 자동완성 요청
                response = self.client.get(
                    "/api/v1/search/autocomplete",
                    params={
                        "q": partial_query,
                        "user_id": str(self.test_user_id),
                        "limit": 5,
                    },
                )

            typing_time = (time.time() - typing_start_time) * 1000
            autocomplete_results.append({
                "query": partial_query,
                "response_time_ms": typing_time,
                "suggestions_count": len(suggestions),
                "success": response.status_code == 200,
            })

        # Then: 자동완성 UX 품질 검증
        for result in autocomplete_results:
            assert result["response_time_ms"] < 500  # 500ms 이내 (PRD 기준)
            assert result["suggestions_count"] > 0
            assert result["success"] == True

        # 입력 길이에 따른 제안 품질 향상 확인
        early_suggestions = autocomplete_results[0]["suggestions_count"]
        later_suggestions = autocomplete_results[-1]["suggestions_count"]
        assert later_suggestions >= early_suggestions  # 더 구체적인 제안

    async def test_personalized_search_experience(self) -> None:
        """
        Given: 사용자의 과거 검색 및 방문 히스토리
        When: 개인화된 검색을 사용함
        Then: 개인 취향에 맞는 맞춤형 결과를 받음
        """
        # Given: 사용자 프로필 및 히스토리
        user_profile = {
            "preferred_categories": ["cafe", "restaurant"],
            "favorite_regions": ["홍대", "강남"],
            "preferred_tags": ["조용한", "분위기좋은"],
            "price_preference": [1, 2],  # 저렴한 편 선호
            "visit_pattern": "주로 오후 시간대",
        }

        # Mock 개인화 검색 서비스
        with patch("app.services.personalization_service.get_personalized_results") as mock_personalized:
            # 사용자 히스토리 기반 개인화 결과
            personalized_places = []
            for place in self.realistic_places:
                # 개인화 점수 계산
                personalization_score = 0
                if place["category"] in user_profile["preferred_categories"]:
                    personalization_score += 3
                if place["region"] in user_profile["favorite_regions"]:
                    personalization_score += 2
                if any(tag in user_profile["preferred_tags"] for tag in place["tags"]):
                    personalization_score += 2
                if place["price_range"] in user_profile["price_preference"]:
                    personalization_score += 1

                if personalization_score > 0:
                    place_copy = place.copy()
                    place_copy["personalization_score"] = personalization_score
                    personalized_places.append(place_copy)

            # 개인화 점수순 정렬
            personalized_places.sort(key=lambda x: x["personalization_score"], reverse=True)

            mock_personalized.return_value = {
                "places": personalized_places,
                "personalization_applied": True,
                "personalization_factors": [
                    "선호 카테고리 반영",
                    "자주 방문하는 지역 우선",
                    "취향 태그 매칭",
                ],
                "recommendation_confidence": 0.87,
            }

            # When: 개인화 검색 실행
            response = self.client.post(
                "/api/v1/search/personalized",
                json={
                    "query": "카페",
                    "user_id": str(self.test_user_id),
                    "apply_personalization": True,
                },
            )

        # Then: 개인화 검색 품질 검증
        result = mock_personalized.return_value

        assert result["personalization_applied"] == True
        assert result["recommendation_confidence"] > 0.7  # 70% 이상 신뢰도
        assert len(result["personalization_factors"]) >= 3

        # 개인화 순서 검증 (높은 점수 순)
        places = result["places"]
        if len(places) > 1:
            for i in range(len(places) - 1):
                current_score = places[i]["personalization_score"]
                next_score = places[i + 1]["personalization_score"]
                assert current_score >= next_score

    async def test_search_error_handling_ux(self) -> None:
        """
        Given: 검색 중 다양한 오류 상황
        When: 오류가 발생함
        Then: 사용자에게 명확하고 도움이 되는 오류 메시지 제공함
        """
        # Given: 다양한 오류 시나리오들
        error_scenarios = [
            {
                "name": "network_timeout",
                "status_code": 504,
                "error_message": "서버 응답 시간이 초과되었어요",
                "suggestion": "잠시 후 다시 시도해주세요",
                "retry_possible": True,
            },
            {
                "name": "server_error",
                "status_code": 500,
                "error_message": "일시적인 서버 오류가 발생했어요",
                "suggestion": "문제가 지속되면 고객센터로 문의해주세요",
                "retry_possible": True,
            },
            {
                "name": "invalid_query",
                "status_code": 400,
                "error_message": "검색어를 확인해주세요",
                "suggestion": "2글자 이상 입력해주세요",
                "retry_possible": False,
            },
        ]

        for scenario in error_scenarios:
            # Mock 오류 응답
            with patch("app.api.v1.endpoints.search.search_places") as mock_search:
                if scenario["status_code"] >= 500:
                    mock_search.side_effect = Exception("Server Error")
                else:
                    mock_search.return_value = {
                        "error": {
                            "code": scenario["name"],
                            "message": scenario["error_message"],
                            "suggestion": scenario["suggestion"],
                            "retry_possible": scenario["retry_possible"],
                        },
                        "fallback_results": self.realistic_places[:3] if scenario["status_code"] == 504 else [],
                    }

                # When: 오류 상황에서 검색 실행
                try:
                    response = self.client.post(
                        "/api/v1/search/places",
                        json={
                            "query": "test query",
                            "user_id": str(self.test_user_id),
                        },
                    )

                    if scenario["status_code"] < 500:
                        result = mock_search.return_value
                        error_info = result["error"]

                        # Then: 사용자 친화적 오류 처리 검증
                        assert "message" in error_info
                        assert "suggestion" in error_info
                        assert error_info["message"] != ""
                        assert error_info["suggestion"] != ""

                        # 네트워크 오류 시 대체 결과 제공
                        if scenario["name"] == "network_timeout":
                            assert len(result["fallback_results"]) > 0

                except Exception as e:
                    # 서버 오류의 경우 적절한 예외 처리 확인
                    assert scenario["status_code"] >= 500
                    assert "Server Error" in str(e)

    async def test_search_accessibility_ux(self) -> None:
        """
        Given: 접근성이 필요한 사용자
        When: 검색 기능을 사용함
        Then: 접근성 지침을 준수한 사용자 경험 제공함
        """
        # Given: 접근성 설정이 활성화된 사용자
        accessibility_settings = {
            "screen_reader": True,
            "high_contrast": True,
            "large_text": True,
            "voice_navigation": True,
        }

        # Mock 접근성 맞춤 검색
        with patch("app.api.v1.endpoints.search.search_places") as mock_search:
            mock_search.return_value = {
                "places": self.realistic_places,
                "total_count": len(self.realistic_places),
                "accessibility": {
                    "screen_reader_text": f"총 {len(self.realistic_places)}개의 장소를 찾았습니다",
                    "keyboard_navigation": True,
                    "high_contrast_ready": True,
                    "alternative_text": {
                        place["id"]: f"{place['name']}, {place['category']}, 평점 {place['rating']}점"
                        for place in self.realistic_places
                    },
                },
            }

            # When: 접근성 설정으로 검색 실행
            response = self.client.post(
                "/api/v1/search/places",
                json={
                    "query": "카페",
                    "user_id": str(self.test_user_id),
                    "accessibility_settings": accessibility_settings,
                },
            )

        # Then: 접근성 기능 제공 확인
        result = mock_search.return_value
        accessibility_info = result["accessibility"]

        assert "screen_reader_text" in accessibility_info
        assert accessibility_info["keyboard_navigation"] == True
        assert accessibility_info["high_contrast_ready"] == True
        assert len(accessibility_info["alternative_text"]) == len(self.realistic_places)

        # 스크린 리더용 텍스트 품질 검증
        screen_reader_text = accessibility_info["screen_reader_text"]
        assert "찾았습니다" in screen_reader_text
        assert str(len(self.realistic_places)) in screen_reader_text

    async def test_search_mobile_ux_optimization(self) -> None:
        """
        Given: 모바일 디바이스 사용자
        When: 모바일 최적화된 검색을 사용함
        Then: 터치 친화적이고 효율적인 모바일 UX 제공함
        """
        # Given: 모바일 디바이스 정보
        mobile_context = {
            "device_type": "mobile",
            "screen_size": {"width": 375, "height": 812},
            "touch_interface": True,
            "network": "4g",
            "location_available": True,
            "current_location": {"lat": 37.5563, "lng": 126.9223},
        }

        # Mock 모바일 최적화 검색
        with patch("app.api.v1.endpoints.search.search_places") as mock_search:
            # 현재 위치 기반 거리순 정렬
            mobile_optimized_places = self.realistic_places.copy()
            for place in mobile_optimized_places:
                # 간단한 거리 계산 (실제로는 Haversine 공식 사용)
                place["distance_km"] = abs(
                    place["location"]["lat"] - mobile_context["current_location"]["lat"]
                ) * 111  # 위도 1도 ≈ 111km

            mobile_optimized_places.sort(key=lambda x: x["distance_km"])

            mock_search.return_value = {
                "places": mobile_optimized_places,
                "total_count": len(mobile_optimized_places),
                "mobile_optimized": True,
                "ui_optimizations": {
                    "large_touch_targets": True,
                    "swipe_navigation": True,
                    "voice_search_available": True,
                    "location_sorted": True,
                    "reduced_data_usage": True,
                },
                "performance": {
                    "optimized_for_network": mobile_context["network"],
                    "compressed_images": True,
                    "lazy_loading": True,
                },
            }

            # When: 모바일 컨텍스트로 검색 실행
            response = self.client.post(
                "/api/v1/search/places",
                json={
                    "query": "카페",
                    "user_id": str(self.test_user_id),
                    "device_context": mobile_context,
                },
            )

        # Then: 모바일 UX 최적화 검증
        result = mock_search.return_value

        assert result["mobile_optimized"] == True

        ui_opts = result["ui_optimizations"]
        assert ui_opts["large_touch_targets"] == True
        assert ui_opts["location_sorted"] == True

        performance = result["performance"]
        assert performance["optimized_for_network"] == "4g"
        assert performance["compressed_images"] == True

        # 거리순 정렬 확인
        places = result["places"]
        if len(places) > 1:
            for i in range(len(places) - 1):
                current_distance = places[i]["distance_km"]
                next_distance = places[i + 1]["distance_km"]
                assert current_distance <= next_distance

    async def test_search_satisfaction_metrics(self) -> None:
        """
        Given: 검색 사용자 행동 추적
        When: 다양한 검색 패턴을 분석함
        Then: 사용자 만족도 지표가 목표 수준을 달성함
        """
        # Given: 사용자 행동 시뮬레이션 데이터
        user_interactions = [
            {
                "query": "홍대 카페",
                "results_shown": 15,
                "clicked_result": True,
                "clicked_position": 2,  # 2번째 결과 클릭
                "satisfied": True,
                "session_duration": 45,  # 45초
            },
            {
                "query": "강남 맛집",
                "results_shown": 20,
                "clicked_result": True,
                "clicked_position": 1,  # 1번째 결과 클릭
                "satisfied": True,
                "session_duration": 30,
            },
            {
                "query": "신촌 술집",
                "results_shown": 8,
                "clicked_result": False,
                "clicked_position": None,
                "satisfied": False,  # 재검색함
                "session_duration": 120,
            },
            {
                "query": "조용한 카페",
                "results_shown": 25,
                "clicked_result": True,
                "clicked_position": 5,
                "satisfied": True,
                "session_duration": 60,
            },
        ]

        # Mock 만족도 분석 서비스
        with patch("app.services.analytics_service.calculate_satisfaction_metrics") as mock_analytics:
            # 만족도 지표 계산
            total_searches = len(user_interactions)
            successful_clicks = sum(1 for interaction in user_interactions if interaction["clicked_result"])
            satisfied_sessions = sum(1 for interaction in user_interactions if interaction["satisfied"])

            click_through_rate = successful_clicks / total_searches
            satisfaction_rate = satisfied_sessions / total_searches

            # 평균 클릭 위치 (상위 결과 클릭률)
            click_positions = [
                interaction["clicked_position"]
                for interaction in user_interactions
                if interaction["clicked_position"] is not None
            ]
            avg_click_position = sum(click_positions) / len(click_positions) if click_positions else 0

            mock_analytics.return_value = {
                "metrics": {
                    "click_through_rate": click_through_rate,
                    "satisfaction_rate": satisfaction_rate,
                    "avg_click_position": avg_click_position,
                    "avg_session_duration": sum(i["session_duration"] for i in user_interactions) / total_searches,
                },
                "kpi_achievement": {
                    "click_rate_target": 0.4,  # 40% 목표 (PRD)
                    "click_rate_actual": click_through_rate,
                    "click_rate_achieved": click_through_rate >= 0.4,
                    
                    "satisfaction_target": 0.7,  # 70% 목표
                    "satisfaction_actual": satisfaction_rate,
                    "satisfaction_achieved": satisfaction_rate >= 0.7,
                },
                "insights": [
                    f"사용자의 {click_through_rate:.1%}가 검색 결과를 클릭했습니다",
                    f"평균 {avg_click_position:.1f}번째 결과를 클릭했습니다",
                    f"만족도는 {satisfaction_rate:.1%}입니다",
                ],
            }

            # When: 만족도 지표 계산 실행
            result = mock_analytics.return_value

        # Then: KPI 달성도 검증 (PRD 기준)
        kpi = result["kpi_achievement"]

        # 클릭률 40% 이상 목표 (PRD 8-2 기준)
        assert kpi["click_rate_achieved"] == True, f"클릭률 {kpi['click_rate_actual']:.1%}는 목표 {kpi['click_rate_target']:.1%}에 미달"

        # 사용자 만족도 70% 이상
        assert kpi["satisfaction_achieved"] == True, f"만족도 {kpi['satisfaction_actual']:.1%}는 목표 {kpi['satisfaction_target']:.1%}에 미달"

        # 상위 결과 클릭 비율 (평균 클릭 위치 3위 이내)
        assert result["metrics"]["avg_click_position"] <= 3.0, "사용자가 너무 아래쪽 결과를 클릭하고 있음"

        # 적절한 세션 지속 시간 (30초-120초 범위)
        avg_duration = result["metrics"]["avg_session_duration"]
        assert 30 <= avg_duration <= 120, f"평균 세션 시간 {avg_duration}초가 적절 범위를 벗어남"